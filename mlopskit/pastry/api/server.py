from curses.ascii import FF
import functools
from mimetypes import suffix_map
from stat import SF_APPEND
import dill
from typing import Optional
from fastapi import Depends, File, Form, FastAPI, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse
import pydantic
from ..dam import Dam
from ..types import Label
import base64
import traceback
import os
from .. import utils
from ..mlflow_rest_client import MLflowRESTClient
from mlopskit.ext.store import YAMLDataSet
import subprocess
from mlopskit.utils import kill9_byport
from mlopskit.ext.tinydb import TinyDB, Query

from datetime import datetime


api = FastAPI()

home_path = os.environ["HOME"]
default_config = os.path.join(home_path, "mlops_config.yml")
default_config_exists = os.path.exists(os.path.join(home_path, "mlops_config.yml"))
try:
    config = YAMLDataSet(default_config).load()
    mlflow_url_local = config.get("mlflow_url_local")
    ignore_ssl_check = config.get("ignore_ssl_check", True)
    mlflow_art_path = config.get("mlflow_art_path", os.getcwd())
    mlflow_client = MLflowRESTClient(
        mlflow_url_local, ignore_ssl_check=ignore_ssl_check
    )
except:
    print(str(traceback.format_exc()))


def get_tail_n_info(n, LOG_FILE):
    """
    tail按行获取
    :param n: 行数
    :return:
    """
    try:
        tail_pipe = os.popen(f"tail -n {n} {LOG_FILE} ")
    except:
        print(f"文件{LOG_FILE}不存在")
        return ""
    else:

        tail_output = iter(tail_pipe.readlines())
        tail_pipe.close()

    return tail_output


class Settings(pydantic.BaseSettings):
    dam: Dam = None
    filestore_dir: str = os.environ.get("FILESTORE_DIR", os.getcwd())


@functools.lru_cache()
def get_settings():
    return Settings()


def deserialize_model(model_bytes):
    return dill.loads(base64.b64decode(model_bytes.encode("ascii")))


@api.post("/models/serving_status")
async def serving_status(
    name: str = Form(...),
    version: str = File(...),
    tail_n: int = File(...),
    tail_logs: str = File(...),
    port: str = File(...),
):
    fd_pid = os.popen("lsof -i:%s|awk '{print $2}'" % str(port))
    pids = fd_pid.read().strip().split("\n")
    if len(pids) > 1:
        port_status = f"port {port} is working"
    else:
        port_status = f"port {port} is not work"
    if tail_logs == "True":
        model_file = mlflow_client.get_model_version_download_url(name, version)
        fname = os.path.basename(model_file)
        dirpath = os.path.dirname(model_file)
        if fname:
            if fname.endswith(".zip"):
                _fpath = fname.split(".")[0]
                _main_path = os.path.join(dirpath, _fpath)
            else:
                _main_path = dirpath
        else:
            return {
                "error_details": "run.log is not exsist",
                "port_status": port_status,
            }
        main_path = os.path.join(mlflow_art_path, _main_path)
        logfile = os.path.join(main_path, "run.log")
        result = []
        for line in get_tail_n_info(n=tail_n, LOG_FILE=logfile):
            if line.strip():
                result.append(line)
        log_str = "\n".join(result)
        return {"log_str": log_str, "port_status": port_status}


@api.post("/models/killservice")
async def kill_model_service(
    port: str = Form(...),
    author: str = Form(...),
):
    metadb_path = os.path.join(mlflow_art_path, "service_ops.json")
    metadb = TinyDB(metadb_path)
    # current date and time
    curDT = datetime.now()
    # current date and time
    date_time = curDT.strftime("%m/%d/%Y, %H:%M:%S")
    print("date and time:", date_time)
    metadb.insert({"port": port, "ops_user": author, "ops_date": date_time})
    try:
        kill9_byport(str(port))
        fd_pid = os.popen("lsof -i:%s|awk '{print $2}'" % str(port))
        pids = fd_pid.read().strip().split("\n")
        if len(pids) < 2:
            return {"service_status": f"{port} 's process is killed"}
        else:
            return {"service_status": f"{port} 's process kill failed"}

    except:
        return {"error_details": str(traceback.format_exc())}


@api.post("/models/serving")
async def serving_model(
    name: str = Form(...),
    version: str = File(...),
    main_py: str = File(...),
    port: str = File(...),
    force: str = File(...),
):
    fd_pid = os.popen("lsof -i:%s|awk '{print $2}'" % str(port))
    pids = fd_pid.read().strip().split("\n")
    if len(pids) > 1:
        if force == "True":
            kill9_byport(str(port))
        else:
            return {"serving_details": "port {} is used".format(port)}
    try:
        model_file = mlflow_client.get_model_version_download_url(name, version)
        fname = os.path.basename(model_file)
        dirpath = os.path.dirname(model_file)
        if fname:
            if fname.endswith(".zip"):
                _fpath = fname.split(".")[0]
                to_be_servemodel = main_py  # os.path.join(dirpath,_fpath,main_py)
                _main_path = os.path.join(dirpath, _fpath)
            else:
                to_be_servemodel = fname  # model_file
                _main_path = dirpath
            main_path = os.path.join(mlflow_art_path, _main_path)
            metadb_path = os.path.join(main_path, "model_meta.json")
            metadb = TinyDB(metadb_path)
            # current date and time
            curDT = datetime.now()

            # current date and time
            date_time = curDT.strftime("%m/%d/%Y, %H:%M:%S")
            print("date and time:", date_time)

            metadb.insert(
                {
                    "name": name,
                    "version": version,
                    "port": port,
                    "creation_date": date_time,
                    "main_py": to_be_servemodel,
                }
            )
            main_command = f"python {to_be_servemodel}"
            logfile = os.path.join(main_path, "run.log")
            # write Makefile
            # logger.debug("Using Docker Base Image %s", bento_service._env._docker_base_image)
            with open(os.path.join(main_path, "run_main.sh"), "w") as f:
                f.write(f"nohup {main_command}  > {logfile} 2>&1 &")

            command = f"cd {main_path} && chmod +x *.sh && ./run_main.sh"
            # p = subprocess.Popen(command ,shell=True)
            utils.timeout_command(command)
            # process = subprocess.Popen([command], env=env,text=True)
            _description = mlflow_client.get_model_version(name, version).description
            if _description:
                new_description = " ".join([_description, f"serving port is {port}"])
            else:
                new_description = f"serving port is {port}"
            mlflow_client.set_model_version_description(name, version, new_description)
        else:
            return {
                "serving_details": f"model {name} or version {version} is not exsits"
            }

    except:
        return {"error_details": str(traceback.format_exc())}


@api.post("/models/push")
async def post_model(
    name: str = Form(...),
    version: str = Form(...),
    if_new_version: str = Form(...),
    model_bytes: str = File(...),
    artifact_location: str = File(...),
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
):
    try:
        if file:
            # file_store = artifact_location
            mlflow_remote_base_path = mlflow_art_path
            file_store = os.path.join(mlflow_remote_base_path, artifact_location)
            utils.make_containing_dirs(file_store)
            filename = await utils.save_file(file, file_store)
            if_zip = filename.endswith(".zip")
            print(if_zip, filename, file_store, "file_store")
            if if_zip:
                file_dir = os.path.splitext(filename)[0]
                dir_name = os.path.dirname(file_store)
                to_dir = os.path.join(dir_name, file_dir)
                print(to_dir, "to_dir")
                utils.unzip(file_store, to_dir)
            # model = deserialize_model(model_bytes)
            # settings.dam.store_model(name, model)
        else:
            model = deserialize_model(model_bytes)
            settings.dam.store_model(name, model)
        if if_new_version == "1":
            return {"status": "ok", "details": f"model version {version} is created!"}
        else:
            return {"status": "ok", "details": f"model version {version} is updated!"}
    except:
        return {"status": "failed", "details": str(traceback.format_exc())}


@api.get("/models/pull")
async def pull_file(name: str, version: str):
    # mlflow_client.get_model_version(name, version)
    source = mlflow_client.get_model_version_download_url(name, version)
    # file_path = "/Users/leepand/Downloads/codes/red_bird.py"
    # d_to = "/Users/leepand/Downloads/codes/mlops-test/red_bird.py"
    mlflow_remote_base_path = mlflow_art_path
    file_to_pull = os.path.join(mlflow_remote_base_path, source)
    return FileResponse(path=file_to_pull, filename=file_to_pull)


@api.delete("/models/{name}")
async def delete_model(name: str, settings: Settings = Depends(get_settings)):
    settings.dam.model_store.delete(name)


@api.get("/models/")
async def get_models(settings: Settings = Depends(get_settings)):

    return settings.dam.model_store.list_names()


class PredictIn(pydantic.BaseModel):
    event: dict
    loop_id: Optional[str] = None


@api.post("/predict/{model_name}")
async def predict(
    model_name: str,
    payload: PredictIn,
    settings: Settings = Depends(get_settings),
):
    prediction = settings.dam.make_prediction(
        event=payload.event, model_name=model_name, loop_id=payload.loop_id
    )
    return jsonable_encoder(prediction)


class LabelIn(pydantic.BaseModel):
    label: str


@api.post("/label/{loop_id}")
async def label(
    loop_id: str,
    payload: LabelIn,
    settings: Settings = Depends(get_settings),
):
    settings.dam.store_label(loop_id=loop_id, label=payload.label)


@api.post("/train/{model_name}")
async def train(
    model_name: str,
    settings: Settings = Depends(get_settings),
):
    n_rows = settings.dam.train_model(model_name=model_name)
    return {"n_rows": n_rows}


@api.post("/_clear/data-store")
async def _clear_data_store(
    settings: Settings = Depends(get_settings),
):
    settings.dam.data_store.clear()
