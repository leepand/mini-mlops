import functools
import requests
import urllib.parse
import os
import pathlib

from mlopskit.utils.file_utils import data_dir, make_containing_dirs
from mlopskit.ext.store.yaml.yaml_data import YAMLDataSet
from mlopskit.pastry.mlflow_rest_client import MLflowRESTClient
from mlopskit.io import sfdb
from mlopskit.config import DEFAULT_SERVER_CONFIG
from ..utils import make_zip, fsync_open


class SDK:
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
        return (
            r.json()
            if as_json and r.headers.get("content-type") == "application/json"
            else r
        )

    def get(self, endpoint, **kwargs):
        return self.request("GET", endpoint, **kwargs)

    def post(self, endpoint, **kwargs):
        return self.request("POST", endpoint, **kwargs)

    def put(self, endpoint, **kwargs):
        return self.request("PUT", endpoint, **kwargs)


class HTTPClient(SDK):
    def __init__(self, host=None, config_file=None, **kwargs):
        super().__init__(host)
        home_path = data_dir()
        default_config = os.path.join(home_path, "mlops_config.yml")
        make_containing_dirs(home_path)

        if config_file is None:
            self.config_file = default_config

        self.config = YAMLDataSet(self.config_file).load()

        model_url = self.config.get("model_url")
        mlflow_url = self.config.get("mlflow_url")
        ignore_ssl_check = self.config.get("ignore_ssl_check", True)
        self.mlflow_art_path = self.config.get("mlflow_art_path", os.getcwd())
        self.mlflow_client = MLflowRESTClient(
            mlflow_url, ignore_ssl_check=ignore_ssl_check, **kwargs
        )

    def push_model(
        self, name: str, version=None, to_push_file=None, run_id=None, tags=None
    ):
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

        if_dir = os.path.isdir(to_push_file)
        if if_dir:
            make_zip(to_push_file, to_push_file)
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
            return self.request(
                method="POST",
                endpoint="models/push",
                as_json=True,
                data={
                    "name": name,
                    "version": version,
                    "if_new_version": str(if_new_version),
                    "artifact_location": source,
                },
                files=_f,
            )

    def pull_model(self, name: str, version: str, save_path: str = os.getcwd()):
        resp = self.request(
            "GET",
            "models/pull",
            params={"name": name, "version": version},
        )
        source = self.mlflow_client.get_model_version_download_url(name, version)
        (path, filename) = os.path.split(source)
        dest_path = os.path.join(save_path, filename)
        if os.sep in dest_path:
            make_containing_dirs(os.path.dirname(dest_path))
        with fsync_open(dest_path, "wb") as file:
            for data in resp.iter_content(chunk_size=1024):
                file.write(data)

        return dest_path

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
        resp = self.request(
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
        resp = self.request(
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

    def set_config(self, config_content, config_path=None):
        default_config = self.config_file
        if config_path:
            yam_engine = YAMLDataSet(os.path.join(config_path, "mlops_config.yml"))
        else:
            yam_engine = YAMLDataSet(default_config)
        yam_engine.save(config_content)

    def get_config(self, config_path=None):
        default_config = self.config_file
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
