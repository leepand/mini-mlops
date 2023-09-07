import functools
from typing import Optional
from fastapi import Depends, File, Form, FastAPI, UploadFile
from fastapi.responses import FileResponse
import pydantic
from ..dam import Dam
import traceback
import os
from .. import utils
from ..mlflow_rest_client import MLflowRESTClient
from mlopskit.ext.store.yaml.yaml_data import YAMLDataSet
from mlopskit.utils import kill9_byport
from mlopskit.utils.read_log import LogReader
from mlopskit.utils.file_utils import data_dir

from datetime import datetime


api = FastAPI()

home_path = data_dir()
default_config = os.path.join(home_path, "mlops_config.yml")
default_config_exists = os.path.exists(os.path.join(home_path, "mlops_config.yml"))
try:
    config = YAMLDataSet(default_config).load()
    mlflow_url_local = config.get("mlflow_url_local")
    ignore_ssl_check = config.get("ignore_ssl_check", True)
    # mlflow_art_path = config.get("mlflow_art_path", os.getcwd())
    mlflow_art_path = os.path.join(home_path, "mlflow_workspace")
    mlflow_client = MLflowRESTClient(
        mlflow_url_local, ignore_ssl_check=ignore_ssl_check
    )
except:
    print(str(traceback.format_exc()))


class Settings(pydantic.BaseSettings):
    dam: Dam = None
    filestore_dir: str = os.environ.get("FILESTORE_DIR", os.getcwd())


@functools.lru_cache()
def get_settings():
    return Settings()


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
        log = LogReader(logfile, buffer_size=tail_n)
        return {"log_str": log.read(), "port_status": port_status}


@api.post("/models/killservice")
async def kill_model_service(
    port: str = Form(...),
    author: str = Form(...),
):
    metadb_path = os.path.join(mlflow_art_path, "service_ops.json")
    # current date and time
    curDT = datetime.now()
    # current date and time
    date_time = curDT.strftime("%m/%d/%Y, %H:%M:%S")
    print("date and time:", date_time)
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
            # current date and time
            curDT = datetime.now()

            # current date and time
            date_time = curDT.strftime("%m/%d/%Y, %H:%M:%S")
            print("date and time:", date_time)

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

        if if_new_version == "1":
            return {"status": "ok", "details": f"model version {version} is created!"}
        else:
            return {"status": "ok", "details": f"model version {version} is updated!"}
    except:
        return {"status": "failed", "details": str(traceback.format_exc())}


@api.get("/models/pull")
async def pull_file(name: str, version: str):
    source = mlflow_client.get_model_version_download_url(name, version)
    mlflow_remote_base_path = mlflow_art_path
    file_to_pull = os.path.join(mlflow_remote_base_path, source)
    return FileResponse(path=file_to_pull, filename=file_to_pull)
