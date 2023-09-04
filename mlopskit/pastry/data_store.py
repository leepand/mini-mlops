from __future__ import annotations
import abc
import contextlib
import dataclasses
import datetime as dt

# import graphlib
import uuid
import pathlib
import re

import sqlalchemy as sqla
import sqlalchemy.orm
from .loop import LoopPart, Event, Features, Prediction, Label, FeatureSet
from mlopskit.ext.tinyflux import TinyFlux, Point
from mlopskit.ext import tinyflux
from . import loop


class DataStore(abc.ABC):
    def build(self):
        ...

    @abc.abstractmethod
    def store(self, kind: str, loop_part: LoopPart):
        ...

    def store_event(self, event: Event):
        return self.store("event", event)

    def store_features(self, features: FeatureSet):
        return self.store("feature_set", features)

    def store_prediction(self, prediction: Prediction):
        return self.store("prediction", prediction)

    def store_label(self, label: Label):
        return self.store("label", label)

    @abc.abstractmethod
    def get(self, kind: str, loop_id: str | uuid.UUID):
        ...

    def get_event(self, loop_id: str | uuid.UUID):
        return self.get("event", loop_id)

    def get_features(self, loop_id: str | uuid.UUID):
        return self.get("features", loop_id)

    def get_prediction(self, loop_id: str | uuid.UUID):
        return self.get("prediction", loop_id)

    def get_label(self, loop_id: str | uuid.UUID):
        return self.get("label", loop_id)

    def clear(self):
        raise NotImplementedError


Base = sqlalchemy.orm.declarative_base()


class LoopPart(Base):
    __abstract__ = True
    loop_id = sqla.Column(sqla.Text(), primary_key=True)
    created_at = sqla.Column(sqla.DateTime(), default=dt.datetime.now)


class Event(LoopPart):
    __tablename__ = "events"
    __table_args__ = {"extend_existing": True}
    content = sqla.Column(sqla.JSON())

    @classmethod
    def from_dataclass(cls, event: Event):
        return cls(loop_id=str(event.loop_id), content=event.content)

    def to_dataclass(self):
        return Event(loop_id=self.loop_id, content=self.content)


class Features1(LoopPart):
    __tablename__ = "features"
    __table_args__ = {"extend_existing": True}
    content = sqla.Column(sqla.JSON())
    model_name = sqla.Column(sqla.Text(), primary_key=True)

    @classmethod
    def from_dataclass(cls, features: Features):
        return cls(
            loop_id=str(features.loop_id),
            content=features.content,
            model_name=features.model_name,
        )

    def to_dataclass(self):
        return Features(
            loop_id=self.loop_id, content=self.content, model_name=self.model_name
        )


class FeatureSet(Base):
    __tablename__ = "feature_set"
    __table_args__ = {"extend_existing": True}
    id = sqla.Column(sqla.Integer, primary_key=True, autoincrement=True)
    author = sqla.Column(sqla.String(20), unique=False, nullable=False)
    uid = sqla.Column(sqla.String(50), unique=False, nullable=False)
    name = sqla.Column(sqla.String(50), unique=False, nullable=False)
    cn_name = sqla.Column(sqla.String(50), unique=False, nullable=False)
    status = sqla.Column(sqla.String(10), unique=False, nullable=False)
    feature_type = sqla.Column(sqla.String(50), unique=False, nullable=False)
    log_type = sqla.Column(sqla.String(50), unique=False, nullable=False)
    version = sqla.Column(sqla.String(10), unique=False, nullable=False)
    content = sqla.Column(sqla.String(200), unique=False, nullable=False)
    created_at = sqla.Column(sqla.DateTime, unique=False, nullable=False)

    @classmethod
    def from_dataclass(cls, feature: FeatureSet):
        return cls(
            author=feature.author,
            name=feature.name,
            cn_name=feature.cn_name,
            uid=feature.uid,
            feature_type=feature.feature_type,
            log_type=feature.log_type,
            status=feature.status,
            version=feature.version,
            content=feature.content,
            created_at=dt.datetime.utcnow(),
        )

    def to_dataclass(self):
        return FeatureSet(
            id=self.id,
            uid=self.uid,
            author=self.author,
            content=self.content,
            name=self.name,
            cn_name=self.cn_name,
            status=self.status,
            version=self.version,
            created_at=self.created_at,
            log_type=self.log_type,
            feature_type=self.feature_type,
        )


class Prediction1(LoopPart):
    __tablename__ = "predictions33"
    content = sqla.Column(sqla.JSON())
    model_name = sqla.Column(sqla.Text(), primary_key=True)

    @classmethod
    def from_dataclass(cls, prediction: Prediction):
        return cls(
            loop_id=str(prediction.loop_id),
            content=prediction.content,
            model_name=prediction.model_name,
        )

    def to_dataclass(self):
        return Prediction(
            loop_id=self.loop_id, content=self.content, model_name=self.model_name
        )


class Prediction(Base):
    __tablename__ = "predictions"
    __table_args__ = {"extend_existing": True}

    id = sqla.Column(sqla.Integer, primary_key=True, autoincrement=True)
    experiment = sqla.Column(sqla.String(50), unique=False, nullable=False)
    predict_type = sqla.Column(sqla.String(50), unique=False, nullable=False)
    log_type = sqla.Column(sqla.String(50), unique=False, nullable=False)
    alternative = sqla.Column(sqla.String(50), unique=False, nullable=False)
    content = sqla.Column(sqla.String(200), unique=False, nullable=False)
    request_id = sqla.Column(sqla.String(100), unique=False, nullable=False)
    created_at = sqla.Column(sqla.DateTime, unique=False, nullable=False)

    @classmethod
    def from_dataclass(cls, prediction: Prediction):
        return cls(
            content=prediction.content,
            predict_type=prediction.predict_type,
            log_type=prediction.log_type,
            experiment=prediction.experiment,
            alternative=prediction.alternative,
            request_id=prediction.request_id,
            created_at=dt.datetime.utcnow(),
        )

    def to_dataclass(self):
        return Prediction(
            id=self.id,
            content=self.content,
            experiment=self.experiment,
            alternative=self.alternative,
            request_id=self.request_id,
            predict_type=self.predict_type,
            log_type=self.log_type,
        )


class Label(LoopPart):
    __tablename__ = "labels"
    __table_args__ = {"extend_existing": True}
    content = sqla.Column(sqla.JSON())

    @classmethod
    def from_dataclass(cls, label: Label):
        return cls(loop_id=str(label.loop_id), content=label.content)

    def to_dataclass(self):
        return Label(loop_id=self.loop_id, content=self.content)


@dataclasses.dataclass
class View:
    path: pathlib.Path

    def __hash__(self):
        return hash(self.name)

    @property
    def name(self):
        return self.path.stem

    @property
    def query(self):
        return self.path.read_text().rstrip().rstrip(";")

    @property
    def cte_names(self):
        pattern = r'"?(?P<table>\w+)"? AS \('
        return {match.group("table") for match in re.finditer(pattern, self.query)}

    @property
    def dependencies(self):
        pattern = r'(FROM|(LEFT|RIGHT|INNER|OUTER)? JOIN) "?(?P<table>\w+)"?'
        tables = {match.group("table") for match in re.finditer(pattern, self.query)}
        return tables - self.cte_names


class TinyFluxStore(DataStore):
    def __init__(self, url):
        self.url = url
        self.engine = TinyFlux(self.url)

    def build(self):
        self.engine = TinyFlux(self.url)

    def store(self, kind, loop_part: loop.LoopPart):
        x_input = loop_part.to_dict()
        _tags = x_input["tags"]
        _tags["data_type"] = kind
        _tags["request_id"] = x_input["loop_id"]
        p = Point(time=x_input["created_at"], tags=_tags, fields=x_input["fields"])
        self.engine.insert(p)

    def get(self, kind, loop_id):
        klass = {
            "event": loop.EventFlux,
            "feature_set": Features,
            "prediction": Prediction,
            "label": Label,
        }[kind]
        with self.session() as session:
            return (
                session.query(klass)
                .filter_by(loop_id=str(loop_id))
                .first()
                .to_dataclass()
            )


class SQLDataStore(DataStore):
    def __init__(self, url):
        self.engine = sqla.create_engine(url)

    def build(self):
        Base.metadata.create_all(self.engine)

        here = pathlib.Path(__file__)
        views = [View(path) for path in here.parent.glob("views/*.sql")]
        views = {view.name: view for view in views}

        dependencies = {view: set() for view in views.values()}
        for view in views.values():
            for dep in view.dependencies & views.keys():
                dependencies[view].add(views[dep])

        # for view in graphlib.TopologicalSorter(dependencies).static_order():
        #    self.engine.execute(sqla.text(f"DROP VIEW IF EXISTS {view.name}"))
        #    self.engine.execute(sqla.text(f"CREATE VIEW {view.name} AS {view.query}"))

    def clear(self):
        with contextlib.closing(self.engine.connect()) as con:
            trans = con.begin()
            for table in reversed(Base.metadata.sorted_tables):
                con.execute(table.delete())
            trans.commit()

    @contextlib.contextmanager
    def session(self):
        session_maker = sqlalchemy.orm.sessionmaker(self.engine)
        try:
            with session_maker.begin() as session:
                yield session
        finally:
            pass

    def store(self, loop_part=None, kind="prediction"):
        row = {
            "event": Event,
            "feature_set": FeatureSet,
            "prediction": Prediction,
            "label": Label,
        }[kind].from_dataclass(loop_part)
        with self.session() as session:
            session.add(row)

    def get(self, kind, loop_id):
        klass = {
            "event": Event,
            "feature_set": FeatureSet,
            "prediction": Prediction,
            "label": Label,
        }[kind]
        with self.session() as session:
            return (
                session.query(klass).filter_by(id=str(loop_id)).first().to_dataclass()
            )
