import yaml
from pydantic import BaseModel
from typing import List, Optional
import os

from structlog import get_logger

logger = get_logger(__name__)

config_path = os.environ.get("MLOPS_CONFIG", os.path.join(os.getcwd(), "config.yml"))

if os.path.exists(config_path):
    try:
        CONFIG = yaml.safe_load(open(config_path, "r"))
    except IOError:
        raise RuntimeError(
            "MLOPS_CONFIG - {0} - is an invalid path".format(config_path)
        )
    except yaml.YAMLError as exc:
        raise RuntimeError("Error in configuration file: {0}".format(str(exc)))
else:
    CONFIG = {
        "mlops_art_basepath": os.environ.get("MLOPS_ART_BASEPATH", os.getcwd()),
        "mlflow_remote_server_uri": os.environ.get(
            "MLFLOW_REMOTE_SERVER_URI", "http://0.0.0.0:8904"
        ),
        "mlflow_local_server_uri": os.environ.get(
            "MLFLOW_LOCAL_SERVER_URI", "http://0.0.0.0:8904"
        ),
        "mlops_sqlite_db": os.environ.get("MLOPS_SQLITE_DB", "mlops.db"),
    }


class ServerOptions(BaseModel):
    # mutable default is ok for pydantic : https://stackoverflow.com/questions/63793662/how-to-give-a-pydantic-list-field-a-default-value
    model_url: Optional[str] = "http://0.0.0.0:3000"
    mlflow_url: Optional[str] = "http://0.0.0.0:8904"
    mlflow_url_local: Optional[str] = "http://0.0.0.0:8904"
    mlflow_url_remote: Optional[str] = "http://54.214.110.168:8904"
    mlflow_url_description: Optional[str] = "mlflow服务端地址"
    mlflow_art_path: Optional[str] = os.getcwd()
    mlflow_art_path_description: Optional[str] = "mlflow服务端工件的存放位置"
    mlops_sqlite_db: Optional[str] = "mlops.db"
    mlops_sqlite_db_description: Optional[str] = "mlops服务端的元数据存储位置及数据库"
    mlops_config_path: Optional[str] = config_path
    mlops_config_path_description: Optional[str] = "该配置文件的存储位置"

    ignore_ssl_check: Optional[bool] = True
    usage: Optional[
        str
    ] = "from mlopskit.ext.store import YAMLDataSet;YAMLDataSet('./config.yml').save(ServerOptions(...).dict())"

    # class Config:
    #    extra = "forbid"


DEFAULT_SERVER_CONFIG = {
    "ignore_ssl_check": True,
    "redis_host": "localhost",
    "redis_port": "6379",
    "redis_ab_db": "15",
    "mlflow_art_path": "/home/ec2-user/models_deploy/campaign-ds/bole_ds_platform/mlworkspace",
    "mlflow_art_path_description": "mlflow服务端工件的存放位置",
    "mlflow_url": "http://1.31.24.138:8904",
    "mlflow_url_description": "mlflow服务端地址",
    "mlflow_url_local": "http://1.31.24.138:8904",
    "mlflow_url_remote": "http://1.31.24.138:8904",
    "mlops_config_path": "/home/ec2-user/models_deploy/campaign-ds/bole_ds_platform/config.yml",
    "mlops_config_path_description": "该配置文件的存储位置",
    "mlops_sqlite_db": "/home/ec2-user/models_deploy/campaign-ds/bole_ds/tests/sql.db",
    "mlops_sqlite_db_description": "mlops服务端的元数据存储位置及数据库",
    "model_url": "http://1.31.24.138:5005",
    "usage": "from mlopskit.ext.store import YAMLDataSet;YAMLDataSet('./config.yml').save(ServerOptions(...).dict())",
}


import argparse
from abc import abstractmethod
from typing import Any, Callable, Dict, Type

from everett import NO_VALUE, ConfigurationMissingError
from everett.manager import ConfigManager, ConfigOSEnv, ListOf, generate_uppercase_key

_config = ConfigManager([])


class ConfigEnv:
    register = True
    on_top = True

    @abstractmethod
    def get(self, key, namespace=None):
        raise NotImplementedError  # pragma: no cover

    def __init_subclass__(cls: Type["ConfigEnv"]):
        if cls.register:
            inst = cls()
            if cls.on_top:
                _config.envs.insert(0, inst)
            else:
                _config.envs.append(inst)


class _ConfigArgParseEnv(ConfigEnv):
    on_top = False

    def __init__(self):
        self.cache = dict()

    def get(self, key, namespace=None):
        name = generate_uppercase_key(key, namespace).lower()
        if name in self.cache:
            return self.cache[name]
        parser = argparse.ArgumentParser()
        parser.add_argument(f"--{name}")
        args, _ = parser.parse_known_args()
        res = getattr(args, name) or NO_VALUE
        self.cache[name] = res
        return res


class _NamespacedOSEnv(ConfigOSEnv, ConfigEnv):
    namespace = "MLOPSKIT"

    def get(self, key, namespace=None):
        return super(_NamespacedOSEnv, self).get(key, namespace or self.namespace)


class Param:
    def __init__(
        self,
        key,
        namespace=None,
        default=NO_VALUE,
        alternate_keys=NO_VALUE,
        doc="",
        parser: Callable = str,
        raise_error=True,
        raw_value=False,
    ):
        self.key = key
        self.namespace = namespace
        self.default = default
        self.alternate_keys = alternate_keys
        self.doc = doc
        self.parser = parser
        self.raise_error = raise_error
        self.raw_value = raw_value

    def __get__(self, instance: "Config", owner: Type["Config"]):
        if instance is None:
            return self
        return _config(
            key=self.key,
            namespace=self.namespace or instance.namespace,
            default=self.default,
            alternate_keys=self.alternate_keys,
            doc=self.doc,
            parser=self.parser,
            raise_error=self.raise_error,
            raw_value=self.raw_value,
        )


class _ConfigMeta(type):
    def __new__(mcs, name, bases, namespace):
        meta = super().__new__(mcs, name + "Meta", (mcs,) + bases, namespace)
        res = super().__new__(meta, name, bases, {})
        return res


class Config(metaclass=_ConfigMeta):
    namespace = None

    @classmethod
    def _try__get__(cls, value, default):
        try:
            return value.__get__(cls, type(cls))
        except ConfigurationMissingError:
            return default

    @classmethod
    def get_params(cls) -> Dict[str, Any]:
        return {
            name: cls._try__get__(value, "--NOT-SET--")
            for name, value in cls.__dict__.items()
            if isinstance(value, Param)
        }

    @classmethod
    def log_params(cls):
        # from ebonite.utils.log import logger
        # logger.debug("%s environment:", cls.__name__)
        logger.debug(f"{cls.__name__} environment:")
        for name, value in cls.get_params().items():
            logger.debug(f"{name}: {value}")


class Core(Config):
    DEBUG = Param("debug", default="false", doc="turn debug on", parser=bool)
    ADDITIONAL_EXTENSIONS = Param(
        "extensions",
        default="",
        doc="comma-separated list of additional mlopskit extensions to load",
        parser=ListOf(str),
        raise_error=False,
    )
    AUTO_IMPORT_EXTENSIONS = Param(
        "auto_import_extensions",
        default="true",
        doc="Set to true to automatically load available extensions on mlopskit import",
        parser=bool,
    )
    RUNTIME = Param(
        "runtime", default="false", doc="is this instance a runtime", parser=bool
    )


class Logging(Config):
    LOG_LEVEL = Param(
        "log_level",
        default="INFO" if not Core.DEBUG else "DEBUG",
        doc="Logging level for mlopskit",
        parser=str,
    )


class Runtime(Config):
    SERVER = Param("server", doc="server for runtime")
    LOADER = Param("loader", doc="interface loader for runtime")


if Core.DEBUG:
    Logging.log_params()
    Core.log_params()
    Runtime.log_params()


class ServerConfig(Config):
    host = Param("host", default="0.0.0.0", parser=str)
    ports = Param("ports", default="5001,5002", parser=ListOf(int))
    workers = Param("workers", default="4", parser=int)
    serving = Param("serving", default="true", parser=bool)
    server_name = Param("server_name", default="recomserver", parser=str)
    prebuild_path = Param("prebuild_path", default="src", parser=str)


SERVER_PORT_CONFIG = {
    "ops_servers": ["recomserver", "rewardserver"],
    "recomserver": {
        "host": "0.0.0.0",
        "ports": [4001],
        "prebuild_path": "src",
        "server_name": "recomserver",
        "serving": True,
        "workers": 4,
    },
    "rewardserver": {
        "host": "0.0.0.0",
        "ports": [5001],
        "prebuild_path": "src",
        "server_name": "rewardserver",
        "serving": True,
        "workers": 4,
    },
}

FRONTEND_PATH = "/Users/leepand/同步空间/codes/mini-mlops/frontend"
SERVER_PATH = "/Users/leepand/同步空间/codes/mini-mlops/mlopskit/server"
