from pyjackson import dumps, loads
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
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from typing import Any, Dict, Iterable, List, Optional, Type, TypeVar
from abc import abstractmethod

from .views import User, AbExpCase, AbExpOps, DataCampaign


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


class SUsers(Base, Attaching):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    mobile = Column(String(11), unique=False, nullable=False)
    password = Column(String(200), unique=False, nullable=False)
    email = Column(String(100), unique=False, nullable=False)
    # role = Column(String(50), unique=False, nullable=False)

    creation_date = Column(DateTime, unique=False, nullable=False)
    abexpcases: Iterable["SAbExpCase"] = relationship(
        "SAbExpCase", back_populates="user"
    )

    def to_obj(self) -> User:
        user = User(
            id=self.id,
            name=self.name,
            mobile=self.mobile,
            creation_date=self.creation_date,
            password=self.password,
            # role=self.role,
            email=self.email,
        )
        return self.attach(user)


class SDataCampaign(Base, Attaching):
    __tablename__ = "data_campaigns"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=False, nullable=False)
    data_campaign_type = Column(String(50), unique=False, nullable=False)
    author = Column(String(50), unique=False, nullable=False)
    description = Column(String(200), unique=False, nullable=False)
    expire_date = Column(DateTime, unique=False, nullable=False)
    online_date = Column(DateTime, unique=False, nullable=False)
    creation_date = Column(DateTime, unique=False, nullable=False)
    campaign_status = Column(Integer, unique=False, nullable=False)

    abexpcase: Iterable["SAbExpCase"] = relationship(
        "SAbExpCase", back_populates="data_campaign"
    )
    # strategys: Iterable['SDataStrategy'] = relationship("SDataStrategy", back_populates="data_campaign")
    # strategy_details: Iterable['SDataStrategyDetails'] = relationship("SDataStrategyDetails", back_populates="data_campaign")

    def to_obj(self) -> DataCampaign:
        p = DataCampaign(
            id=self.id,
            name=self.name,
            data_campaign_type=self.data_campaign_type,
            author=self.author,
            description=self.description,
            expire_date=self.expire_date,
            online_date=self.online_date,
            creation_date=self.creation_date,
            campaign_status=self.campaign_status,
        )
        return self.attach(p)


class SAbExpCase(Base, Attaching):
    __tablename__ = "abexpcases"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(200), unique=False, nullable=False)
    app_type = Column(String(50), unique=False, nullable=False)
    data_campaign_id = Column(Integer, ForeignKey("data_campaigns.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    creation_date = Column(DateTime, unique=False, nullable=False)

    data_campaign = relationship("SDataCampaign", back_populates="abexpcase")
    user = relationship("SUsers", back_populates="abexpcases")
    abexpops: Iterable["SAbExpOps"] = relationship(
        "SAbExpOps", back_populates="abexpcase"
    )
    # strategys: Iterable['SDataStrategy'] = relationship("SDataStrategy", back_populates="abexpcase")

    def to_obj(self) -> AbExpCase:
        p = AbExpCase(
            id=self.id,
            name=self.name,
            data_campaign_id=self.data_campaign_id,
            description=self.description,
            app_type=self.app_type,
            user_id=self.user_id,
            creation_date=self.creation_date,
        )
        return self.attach(p)


class SAbExpOps(Base, Attaching):
    __tablename__ = "abexpopss"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=False, nullable=False)
    alt_name = Column(String(50), unique=False, nullable=False)
    exposure_ratio = Column(String(20), unique=False, nullable=False)
    model_name = Column(String(50), unique=False, nullable=False)
    model_id = Column(Integer, unique=False, nullable=False)  # strategy-id 无策略时为模型id或其他
    ab_id = Column(Integer, ForeignKey("abexpcases.id"), nullable=False)
    description = Column(String(200), unique=False, nullable=False)
    creation_date = Column(DateTime, unique=False, nullable=False)

    abexpcase = relationship("SAbExpCase", back_populates="abexpops")
    __table_args__ = (
        UniqueConstraint("alt_name", "ab_id", name="ab_id_altname_and_ref"),
    )

    def to_obj(self) -> AbExpOps:
        p = AbExpOps(
            id=self.id,
            name=self.name,
            alt_name=self.alt_name,
            exposure_ratio=self.exposure_ratio,
            model_name=self.model_name,
            model_id=self.model_id,
            ab_id=self.ab_id,
            description=self.description,
            creation_date=self.creation_date,
        )
        return self.attach(p)
