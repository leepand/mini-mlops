from .views import FeatureModel, FeatureBase, FeatureSet
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


class SFeatureBase(Base, Attaching):
    __tablename__ = "features"
    id = Column(Integer, primary_key=True, autoincrement=True)
    author = Column(String(50), unique=False, nullable=False)
    feature_en = Column(String(50), unique=True, nullable=False)
    feature_cn = Column(String(50), unique=False, nullable=False)
    feature_cat = Column(String(50), unique=False, nullable=False)
    feature_type = Column(String(50), unique=False, nullable=False)
    gen_freq = Column(String(50), unique=False, nullable=False)
    gen_from = Column(String(50), unique=False, nullable=False)
    status = Column(String(50), unique=False, nullable=False)
    description = Column(String(200), unique=False, nullable=False)
    created_at = Column(DateTime, unique=False, nullable=False)
    updated_at = Column(DateTime, unique=False, nullable=False)

    featuremodel: Iterable["SFeatureModel"] = relationship(
        "SFeatureModel", back_populates="featurebase"
    )

    def to_obj(self) -> FeatureBase:
        p = FeatureBase(
            id=self.id,
            author=self.author,
            feature_en=self.feature_en,
            feature_cn=self.feature_cn,
            status=self.status,
            feature_cat=self.feature_cat,
            feature_type=self.feature_type,
            gen_freq=self.gen_freq,
            gen_from=self.gen_from,
            description=self.description,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
        return self.attach(p)


class SFeatureModel(Base, Attaching):
    __tablename__ = "featuremodel"
    id = Column(Integer, primary_key=True, autoincrement=True)
    author = Column(String(50), unique=False, nullable=False)
    name = Column(String(50), unique=False, nullable=False)
    version = Column(String(50), unique=False, nullable=False)
    status = Column(String(50), unique=False, nullable=False)
    description = Column(String(200), unique=False, nullable=False)
    created_at = Column(DateTime, unique=False, nullable=False)
    updated_at = Column(DateTime, unique=False, nullable=False)

    feature_id = Column(Integer, ForeignKey("features.id"))
    # feature_model = relationship("SFeatureBase")
    featurebase = relationship("SFeatureBase", back_populates="featuremodel")

    __table_args__ = (
        UniqueConstraint("name", "version", "feature_id", name="feature_model_version"),
    )

    def to_obj(self) -> FeatureModel:
        p = FeatureModel(
            id=self.id,
            name=self.name,
            author=self.author,
            version=self.version,
            status=self.status,
            feature_id=self.feature_id,
            description=self.description,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
        return self.attach(p)


class SFeatureSet(Base, Attaching):
    __tablename__ = "feature_set"
    id = Column(Integer, primary_key=True, autoincrement=True)
    author = Column(String(20), unique=False, nullable=False)
    uid = Column(String(50), unique=False, nullable=False)
    name = Column(String(50), unique=False, nullable=False)
    cn_name = Column(String(50), unique=False, nullable=False)
    status = Column(String(10), unique=False, nullable=False)
    feature_type = Column(String(50), unique=False, nullable=False)
    log_type = Column(String(50), unique=False, nullable=False)
    version = Column(String(10), unique=False, nullable=False)
    content = Column(String(200), unique=False, nullable=False)
    created_at = Column(DateTime, unique=False, nullable=False)

    def to_obj(self) -> FeatureSet:
        p = FeatureSet(
            id=self.id,
            author=self.author,
            uid=self.uid,
            name=self.name,
            cn_name=self.cn_name,
            status=self.status,
            feature_type=self.feature_type,
            log_type=self.log_type,
            version=self.version,
            content=self.content,
            created_at=self.created_at,
        )
        return self.attach(p)
