# from pyjackson.decorators import make_string, type_field
import datetime
from dataclasses import dataclass
from typing import Dict, Any, Optional
import datetime as dt


@dataclass
class User:
    name: str
    mobile: str = None
    password: str = None
    email: str = None
    role: str = None
    id: int = None
    creation_date: datetime.datetime = None


@dataclass
class AbExpCase:
    name: str
    data_campaign_id: int = None
    description: str = None
    id: int = None
    app_type: str = None
    user_id: int = None
    creation_date: datetime.datetime = None


@dataclass
class AbExpOps:
    name: str
    alt_name: str
    exposure_ratio: str = (None,)
    id: int = None
    model_id: int = None
    model_name: str = None
    description: str = None
    ab_id: int = None
    creation_date: datetime.datetime = None


@dataclass
class DataCampaign:
    name: str
    author: str
    description: str = None
    data_campaign_type: str = None
    id: int = None
    campaign_status: int = None
    online_date: datetime.datetime = None
    expire_date: datetime.datetime = None
    creation_date: datetime.datetime = None


@dataclass
class Prediction:
    content: str
    predict_type: str
    log_type: str
    experiment: str
    alternative: str
    request_id: str
    id: int = None
    created_at: datetime.datetime = None


@dataclass
class Inquiries:
    name: str
    sqlscript: str
    id: int = None
    created_at: datetime.datetime = None


@dataclass
class FeatureBase:
    author: str
    feature_en: str
    feature_cn: str
    feature_cat: str
    feature_type: str
    gen_freq: str
    gen_from: str
    status: str
    description: str
    created_at: datetime.datetime = None
    updated_at: datetime.datetime = None
    id: int = None


@dataclass
class FeatureModel:
    author: str
    id: int = None
    description: str = None
    status: str = None
    name: str = None
    version: str = None
    feature_id: int = None
    created_at: datetime.datetime = None
    updated_at: datetime.datetime = None


@dataclass
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
    created_at: datetime.datetime = None
