import datetime as dt
import dataclasses
import dataclasses_json
import uuid
from typing import Optional, Union


@dataclasses.dataclass(frozen=False)
class LoopPart(dataclasses_json.DataClassJsonMixin):
    created_at: dt.datetime = dataclasses.field(
        default_factory=dt.datetime.now, init=False
    )


@dataclasses.dataclass(frozen=False)
class Event(LoopPart):
    content: dict
    loop_id: Optional[str] = None

    def __post_init__(self):
        if self.loop_id is None:
            self.loop_id = str(uuid.uuid4())


@dataclasses.dataclass(frozen=False)
class EventFlux(LoopPart):
    tags: dict
    fields: dict
    loop_id: Optional[str] = None

    def __post_init__(self):
        if self.loop_id is None:
            self.loop_id = str(uuid.uuid4())


@dataclasses.dataclass(frozen=False)
class Features(LoopPart):
    content: dict
    model_name: str
    loop_id: str


@dataclasses.dataclass(frozen=False)
class Prediction2(LoopPart):
    content: str
    model_name: str
    loop_id: str


@dataclasses.dataclass(frozen=False)
class Prediction(LoopPart):
    content: str
    predict_type: str
    experiment: str
    alternative: str
    request_id: str
    log_type: str
    # id: int


@dataclasses.dataclass(frozen=False)
class Label(LoopPart):
    content: str
    loop_id: str


@dataclasses.dataclass(frozen=False)
class FeatureSet:
    author: str
    id: int = None
    uid: str = None
    name: str = None
    status: str = None
    cn_name: str = None
    feature_type: str = None
    log_type: str = None
    version: str = None
    content: str = None
    created_at: dt.datetime = None
