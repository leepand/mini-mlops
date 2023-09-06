from .views import Prediction, Inquiries
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from abc import abstractmethod
from typing import Any, Dict, Iterable, List, Optional, Type, TypeVar

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Float,
    CheckConstraint,
)

SQL_OBJECT_FIELD = "_sqlalchemy_object"

Base = declarative_base()

Mem_Choices = ["ADMIN", "TESTER", "DEV"]


T = TypeVar("T")
S = TypeVar("S", bound="Attaching")


class Attaching:
    id = ...
    name = ...

    def attach(self, obj):
        setattr(obj, SQL_OBJECT_FIELD, self)
        return obj

    @classmethod
    @abstractmethod
    def get_kwargs(cls, obj: T) -> dict:
        pass  # pragma: no cover

    @abstractmethod
    def to_obj(self) -> T:
        pass  # pragma: no cover


class SInquiries(Base, Attaching):
    __tablename__ = "sqlinquiries"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=False, nullable=False)
    sqlscript = Column(String(2000), unique=False, nullable=False)
    created_at = Column(DateTime, unique=False, nullable=False)

    def to_obj(self) -> Inquiries:
        p = Inquiries(
            id=self.id,
            name=self.name,
            sqlscript=self.sqlscript,
            created_at=self.created_at,
        )
        return self.attach(p)


class SPrediction(Base, Attaching):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment = Column(String(50), unique=False, nullable=False)
    predict_type = Column(String(50), unique=False, nullable=False)
    log_type = Column(String(50), unique=False, nullable=False)
    alternative = Column(String(50), unique=False, nullable=False)
    content = Column(String(200), unique=False, nullable=False)
    request_id = Column(String(100), unique=False, nullable=False)
    created_at = Column(DateTime, unique=False, nullable=False)

    def to_obj(self) -> Prediction:
        p = Prediction(
            id=self.id,
            experiment=self.experiment,
            predict_type=self.predict_type,
            log_type=self.log_type,
            alternative=self.alternative,
            content=self.content,
            request_id=self.request_id,
            created_at=self.created_at,
        )
        return self.attach(p)
