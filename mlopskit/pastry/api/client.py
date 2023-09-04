import urllib.parse
import functools

import dill
import requests
import base64
from mlopskit.ext.tinydb import TinyDB, Query
from ..mlflow_rest_client import MLflowRESTClient
from mlopskit.ext.store import YAMLDataSet
from ..data_store import DataStore, SQLDataStore, TinyFluxStore
import os
import pathlib
from .. import utils
from mlopskit.utils.file_utils import path_to_local_sqlite_uri
from mlopskit.io import sfdb
import hirlite

import getpass

from ..utils import fsync_open, mkdir_exists_ok

default_user_name = getpass.getuser()
from mlopskit.config import DEFAULT_SERVER_CONFIG


def serialize_model(model):
    return base64.b64encode(dill.dumps(model)).decode("ascii")


class SDK:
    def __init__(self, host):
        self.host = host

    def _request(self, method, endpoint, **kwargs):
        r = requests.request(
            method=method, url=urllib.parse.urljoin(self.host, endpoint), **kwargs
        )
        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            try:
                raise ValueError(r.json()) from e
            except requests.exceptions.JSONDecodeError:
                raise e
        return r


class SDK2:
    def __init__(self, host: str):
        self.host = host

    @functools.lru_cache(maxsize=None)
    def session(self):
        s = requests.Session()
        return s

    def request(self, method, endpoint, as_json=True, session=None, **kwargs):
        r = (session or self.session()).request(
            method=method, url=urllib.parse.urljoin(self.host, endpoint), **kwargs
        )
        r.raise_for_status()
        return r.json() if as_json else r

    def get(self, endpoint, **kwargs):
        return self.request("GET", endpoint, **kwargs)

    def post(self, endpoint, **kwargs):
        return self.request("POST", endpoint, **kwargs)

    def put(self, endpoint, **kwargs):
        return self.request("PUT", endpoint, **kwargs)


class ModelsSDK(SDK):
    def __init__(self, host, mlflow_client):
        super().__init__(host=host)
        self.mlflow_client = mlflow_client

    def push(
        self,
        name: str,
        version=None,
        to_push_file=None,
        push_type="file",
        experiment_id=None,
        run_id=None,
        create_version=True,
        tags=None,
        model=None,
    ):

        VALID_PUSH_TYPES = ("pickle", "file")
        assert (
            push_type in VALID_PUSH_TYPES
        ), f"push type {push_type} not supported. Valid push types are {VALID_PUSH_TYPES}"
        # if if self.mlflow_server:
        if tags:
            model = self.mlflow_client.get_or_create_model(name, tags=tags)
        else:
            model = self.mlflow_client.get_or_create_model(name)

        if run_id:
            run = self.mlflow_client.get_run(run_id)
            experiment_id = run.experiment_id
            experiment = self.mlflow_client.get_experiment(experiment_id)
        else:
            if version:
                model_version = self.mlflow_client.get_model_version(name, version)
                run_id = model_version.run_id
                run = self.mlflow_client.get_run(run_id)
                experiment_id = run.experiment_id
                experiment = self.mlflow_client.get_experiment(experiment_id)

            else:
                experiment = self.mlflow_client.get_or_create_experiment(name)
                experiment_id = experiment.id
                run = self.mlflow_client.create_run(experiment_id)
                run_id = str(run.id)

        # get artifact_loaction
        artifact_location = experiment.artifact_location
        run_id = str(run_id)
        if push_type == "pickle":
            db = TinyDB(f"model_meta_{name}.json")
            MODEL = Query()
            model_info = db.search(MODEL.name == name)
            if model_info:
                maxVesion = max(model_info, key=lambda x: x["version"])
                version = maxVesion["version"] + 1.0
            else:
                version = 1.0
            db.insert({"name": name, "version": version})
            if create_version:
                source = os.path.join(
                    artifact_location, run_id, f"model_meta_{name}.json"
                )
                model_version = self.mlflow_client.create_model_version(
                    name, source=source, run_id=run_id
                )
                _version = model_version
                if_new_version = "1"

            else:
                if_new_version = "0"
                _version = version
            with open(f"model_meta_{name}.json", "rb") as f:
                _f = {"file": f}
                return self._request(
                    "POST",
                    "models/push",
                    data={
                        "name": name,
                        "version": _version,
                        "if_new_version": str(if_new_version),
                        "model_bytes": serialize_model(model),
                        "artifact_location": source,
                    },
                    files=_f,
                )
        elif push_type == "file":
            if_dir = os.path.isdir(to_push_file)
            if if_dir:
                utils.make_zip(to_push_file, to_push_file)
                source = os.path.join(artifact_location, run_id, f"{to_push_file}.zip")
                local_file = f"{to_push_file}.zip"
            else:
                source = os.path.join(artifact_location, run_id, to_push_file)
                local_file = to_push_file

            if_new_version = "0"
            if version is None:
                new_model_version = self.mlflow_client.create_model_version(
                    name, source=source, run_id=run_id
                )
                version = new_model_version.version
                if_new_version = "1"

            with open(local_file, "rb") as f:
                _f = {"file": f}
                return self._request(
                    "POST",
                    "models/push",
                    data={
                        "name": name,
                        "version": version,
                        "if_new_version": str(if_new_version),
                        "model_bytes": serialize_model(model),
                        "artifact_location": source,
                    },
                    files=_f,
                )

    def pull(self, name: str, version: str, save_path: str = os.getcwd()):
        resp = self._request(
            "GET",
            "models/pull",
            params={"name": name, "version": version},
        )
        source = self.mlflow_client.get_model_version_download_url(name, version)
        (path, filename) = os.path.split(source)
        dest_path = os.path.join(save_path, filename)
        if os.sep in dest_path:
            mkdir_exists_ok(os.path.dirname(dest_path))
        with fsync_open(dest_path, "wb") as file:
            for data in resp.iter_content(chunk_size=1024):
                file.write(data)

        # (path, filename) = os.path.split(source)
        # with open(os.path.join(save_path, filename), "wb") as f:
        #    f.write(resp.content)
        return True

    def delete(self, name: str):
        return self._request("DELETE", f"models/{name}")

    def list_models(self):
        return self._request("GET", "models").json()

    def serving(
        self,
        name: str,
        version: str,
        main_py: str = None,
        port: str = None,
        force="False",
    ):
        VALID_FORCE_TYPES = ("True", "False")
        assert (
            force in VALID_FORCE_TYPES
        ), f"force type {force} not supported. Valid force types are {VALID_FORCE_TYPES}"
        resp = self._request(
            "POST",
            "models/serving",
            data={
                "name": name,
                "version": version,
                "main_py": main_py,
                "port": port,
                "force": force,
            },
        )
        if resp:
            return resp.json()
        else:
            return resp

    def serving_status(
        self, name: str, version: str, port: str, tail_logs="True", tail_n=100
    ):
        resp = self._request(
            "POST",
            "models/serving_status",
            data={
                "name": name,
                "version": version,
                "tail_n": tail_n,
                "tail_logs": tail_logs,
                "port": port,
            },
        )
        if resp:
            return resp.json()
        else:
            return resp

    def predict(self, name, port, payload):
        model_host = ":".join(self.host.split(":")[0:-1])
        model_url = ":".join([model_host, port])
        resp = requests.post(f"{model_url}/predict/{name}", json=payload)
        return resp.json()

    def killservice(self, port):
        resp = self._request(
            "POST",
            "models/killservice",
            data={"port": str(port), "author": default_user_name},
        )
        return resp.json()


class HTTPClient(SDK):
    def __init__(self, host=None, config=None, **kwargs):
        super().__init__(host=host)
        self._config = config
        home_path = os.environ["HOME"]
        default_config = os.path.join(home_path, "mlops_config.yml")
        default_config_exists = os.path.exists(
            os.path.join(home_path, "mlops_config.yml")
        )
        if not default_config_exists:
            default_config = None
        if self._config:
            _config_file = self._config
        elif default_config:
            _config_file = default_config
        else:
            _config_file = None
        if _config_file:
            self.config = YAMLDataSet(_config_file).load()
            model_url = self.config.get("model_url")
            mlflow_url = self.config.get("mlflow_url")
            ignore_ssl_check = self.config.get("ignore_ssl_check", True)
            self.mlflow_art_path = self.config.get("mlflow_art_path", os.getcwd())
            self.mlflow_client = MLflowRESTClient(
                mlflow_url, ignore_ssl_check=ignore_ssl_check, **kwargs
            )
        else:
            model_url = host
            self.mlflow_client = None
            self.mlflow_art_path = os.getcwd()

        if host:
            model_url = host

        self.models = ModelsSDK(host=model_url, mlflow_client=self.mlflow_client)

    # @property
    # def mlflow_client(self,ignore_ssl_check=True,**kwargs):
    #    return MLflowRESTClient("http://54.214.110.168:8904",
    #                            ignore_ssl_check=ignore_ssl_check,
    #                            **kwargs)

    def predict(self, event, model_name, loop_id=None):
        payload = {"event": event}
        if loop_id is not None:
            payload["loop_id"] = loop_id
        return self._request("POST", f"predict/{model_name}", json=payload).json()

    def label(self, loop_id, label):
        self._request("POST", f"label/{loop_id}", json={"label": label})

    def train(self, model_name):
        return self._request("POST", f"train/{model_name}").json()

    def set_config(self, config_content, config_path=None):
        home_path = os.environ["HOME"]
        default_config = os.path.join(home_path, "mlops_config.yml")
        if config_path:
            yam_engine = YAMLDataSet(os.path.join(config_path, "mlops_config.yml"))
        else:
            yam_engine = YAMLDataSet(default_config)
        yam_engine.save(config_content)

    def get_config(self, config_path=None):
        home_path = os.environ["HOME"]
        default_config = os.path.join(home_path, "mlops_config.yml")
        if config_path:
            path = pathlib.Path(config_path)
            if path.is_file():
                yam_engine = YAMLDataSet(config_path)
            else:
                yam_engine = YAMLDataSet(os.path.join(config_path, "mlops_config.yml"))
        else:
            yam_engine = YAMLDataSet(default_config)
        try:
            config = yam_engine.load()
        except:
            config = DEFAULT_SERVER_CONFIG

        return config

    def get_model_meta_db(self):
        init_db_file = os.path.join(self.mlflow_art_path, "model_meta.db")
        return init_db_file

    def get_model_meta(self, model_name):
        init_db_file = os.path.join(self.mlflow_art_path, "model_meta.db")
        with sfdb.Database(filename=init_db_file) as db:
            model_key = f"{model_name}:port"
            meta = db.get(model_key)
        return meta

    def update_model_meta(self, model_name, **kwargs):
        _kwargs = kwargs.copy()
        VALID_MODEL_STATUS = ("stoped", "running")
        status = _kwargs.pop("status", "running")
        assert (
            status in VALID_MODEL_STATUS
        ), f"model service status: {status} not supported. Valid model service status are {VALID_MODEL_STATUS}"
        init_db_file = os.path.join(self.mlflow_art_path, "model_meta.db")

        version = _kwargs.pop("version", None)
        # port = _kwargs.get("port")
        # status = _kwargs.get("status","running")

        with sfdb.Database(filename=init_db_file) as db:
            model_key = f"{model_name}:port"
            meta = db.get(model_key)
            _kwargs["status"] = status
            if meta is None:
                meta = {}
                if version:
                    meta[version] = {}
                    for k, v in _kwargs.items():
                        meta[version][k] = v
                else:
                    for k, v in _kwargs.items():
                        meta[k] = v
                # db[model_key] = {
                #    "latest_version": version,
                #    "port": port,
                #    "status": status,
                # }
            else:
                if version:
                    if not meta.get(version):
                        meta[version] = {}
                    for k, v in _kwargs.items():
                        meta[version][k] = v
                else:
                    for k, v in _kwargs.items():
                        meta[k] = v
                # if version is not None:
                #    meta["latest_version"] = version
                # if port is not None:
                #    meta["port"] = port
                # meta["status"] = status
            db[model_key] = meta

    def build_data_store(self, name, version, db_type="sqlite", return_type="dbobj"):
        VALID_DB_TYPES = ("tiny", "sqlite", "postgres")
        assert (
            db_type in VALID_DB_TYPES
        ), f"DB cache type {db_type} not supported. Valid db types are {VALID_DB_TYPES}"
        db_base_path = self.mlflow_art_path
        source = self.mlflow_client.get_model_version_download_url(name, version)
        (path, filename) = os.path.split(source)

        if db_type == "tiny":
            db_file = os.path.join(db_base_path, path, "tinyflux_logs.db")
            db_store = TinyFluxStore(db_file)
        elif db_type == "sqlite":
            db_file = os.path.join(db_base_path, path, "sqlite_logs.db")
            if return_type == "dbobj":
                db_store = SQLDataStore(path_to_local_sqlite_uri(db_file))
                db_store.build()
            else:
                db_store = path_to_local_sqlite_uri(db_file)
        else:
            db_store = None
        return db_store

    def build_cache_store(
        self,
        name,
        version,
        db_name="rlite_model.cache",
        db_type="rlite",
        return_type="dbobj",
    ):
        VALID_DB_TYPES = ("rlite", "redis", "diskcache", "sfdb")
        assert (
            db_type in VALID_DB_TYPES
        ), f"DB cache type {db_type} not supported. Valid db types are {VALID_DB_TYPES}"
        VALID_RETURN_TYPES = ("dblink", "dbobj")
        assert (
            return_type in VALID_RETURN_TYPES
        ), f"Return type {return_type} not supported. Valid return types are {VALID_RETURN_TYPES}"
        db_base_path = self.mlflow_art_path
        source = self.mlflow_client.get_model_version_download_url(name, version)
        (path, filename) = os.path.split(source)
        db_file = os.path.join(db_base_path, path, db_name)
        if db_type == "rlite":
            db_store = hirlite.Rlite(db_file, encoding="utf8")
        elif db_type == "diskcache":
            import diskcache as dc

            db_store = dc.Cache(db_file)
        elif db_type == "sfdb":
            from mlopskit.io import sfdb

            db_store = sfdb.Database(filename=db_file)

        else:
            db_store = None

        if return_type == "dblink":
            return db_file
        else:
            return db_store
