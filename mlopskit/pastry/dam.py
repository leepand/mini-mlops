import datetime as dt
import dill
import json
import pydantic
from typing import Optional, List

from .training import Regime
from .model_store import ModelStore
from .data_store import DataStore
from .model_envelope import ModelEnvelope
from .utils import Featurizer, Learner
from .loop import Event, Prediction, Label
import pickle

from abc import ABCMeta


class Dam(metaclass=ABCMeta):  # (pydantic.BaseSettings):
    def __init__(self, model_store: ModelStore = None, data_store: DataStore = None):
        self.model_store = model_store
        self.data_store = data_store

    def _build(self):
        self.model_store._build()
        self.data_store._build()

    def build(self):
        self.model_store.build()
        self.data_store.build()

    @property
    def http_server(self):
        from .api.server import api, Settings, get_settings

        def get_settings_override():
            return Settings(dam=self)

        api.dependency_overrides[get_settings] = get_settings_override

        return api

    def store_model(self, name, model):

        if self.model_store.get(name):
            raise ValueError(f"'{name}' already exists")

        model_envelope = ModelEnvelope(
            name=name,
            is_featurizer=isinstance(model, Featurizer),
            is_learner=isinstance(model, Learner),
            model_bytes=dill.dumps(model),
        )
        self.model_store.store(model_envelope)

    def make_prediction(
        self, event: dict, model_name: str, loop_id: Optional[str] = None
    ):
        model_envelope = self.model_store.get(model_name)
        model = dill.loads(model_envelope.model_bytes)
        event = Event(content=event, loop_id=loop_id)
        prediction = Prediction(
            content=model.predict(event.content.copy()),
            model_name=model_name,
            loop_id=event.loop_id,
        )
        self.data_store.store_event(event)
        self.data_store.store_prediction(prediction)
        return prediction

    def store_label(self, loop_id: str, label: str):
        new_label = Label(content=label, loop_id=loop_id)
        self.data_store.store_label(new_label)

        # Check if ASAP learning is switched on
        if not Regime.ASAP in self.training_regimes:
            return

        # Train all models which make a prediction for this loop_id
        event = self.data_store.get_event(loop_id)
        sql = "SELECT model_name FROM predictions WHERE loop_id IS NOT NULL"

        for row in self.data_store.engine.execute(sql):
            row = dict(row._mapping.items())
            model_envelope = self.model_store.get(row["model_name"])
            if model_envelope.is_featurizer:
                raise ValueError("Models that featurize are not supported yet")
            model = dill.loads(model_envelope.model_bytes)
            model.learn(event.content, float(label))
            model_envelope.last_label_created_at = new_label.created_at
            model_envelope.model_bytes = dill.dumps(model)
            self.model_store.store(model_envelope)

    def load_training_data(self, since: dt.datetime = None):

        sql = "SELECT * FROM labelled_events WHERE event IS NOT NULL"
        if since:
            sql += f" AND label_created_at > '{since}'"

        for row in self.data_store.engine.execute(sql):
            row = dict(row._mapping.items())
            yield (
                dt.datetime.fromisoformat(row["label_created_at"]),
                json.loads(row["event"]),
                float(row["label"].strip('"')),
            )

    def train_model(self, model_name: str):
        model_envelope = self.model_store.get(model_name)
        if model_envelope.is_featurizer:
            raise ValueError("Models that featurize are not supported yet")
        if not model_envelope.is_learner:
            raise ValueError("Model can't learn")

        training_data = self.load_training_data(
            since=model_envelope.last_label_created_at
        )
        n_training_data = 0
        model = None
        for at, x, y in training_data:
            if model is None:
                model = dill.loads(model_envelope.model_bytes)
            model.learn(x, y)
            n_training_data += 1

        if n_training_data:
            model_envelope.last_label_created_at = at
            model_envelope.model_bytes = dill.dumps(model)
            self.model_store.store(model_envelope)

        return n_training_data
