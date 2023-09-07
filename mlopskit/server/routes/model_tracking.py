from .. import app, auth, sql_db, mlflow_client
from flask import request, Response, send_file, make_response, Markup
from flask_cors import cross_origin
import datetime
import traceback
import json
import os
import nbformat
from mlopskit.ext import format_sql

import sys

# Py2k compat.
if sys.version_info[0] == 2:
    PY2 = True
    binary_types = (buffer, bytes, bytearray)
    decode_handler = "replace"
    numeric = (int, long, float)
    unicode_type = unicode
    from StringIO import StringIO
else:
    PY2 = False
    binary_types = (bytes, bytearray)
    decode_handler = "backslashreplace"
    numeric = (int, float)
    unicode_type = str
    from io import StringIO

# 1. Import the exporter
from nbconvert import HTMLExporter

from sqlalchemy_paginator import Paginator
from pyjackson import deserialize, serialize

from .response import Response
from structlog import get_logger
from ..utils.misc import (
    del_file,
    process_files,
    is_valid_subpath,
    get_parent_directory,
    cat_file_content,
)
from mlopskit.utils.file_utils import path_to_local_sqlite_uri
from mlopskit.io import sfdb

from mlflow.protos.service_pb2 import ListExperiments
from mlflow.protos.model_registry_pb2 import (
    ListRegisteredModels,
    GetRegisteredModel,
    GetLatestVersions,
    GetModelVersion,
    SearchModelVersions,
    TransitionModelVersionStage,
)

from mlflow.protos.service_pb2 import GetExperiment
from mlflow.protos.service_pb2 import SearchRuns, GetRun

from mlflow.utils.proto_json_utils import message_to_json
from mlopskit.config import CONFIG
from werkzeug.utils import secure_filename

from ..models.monitormodels import SPrediction, SInquiries

from .. import mlops_art_basepath

# from ..models.database import SysModelInit
from ..models.mlmonitorinit import MonitorModelInit

logger = get_logger(__name__)

rsp = Response()

model_meta_file = os.path.join(mlops_art_basepath, "model_meta.db")


@app.route("/api/experiments/get_model_experiments", methods=["GET"])
@cross_origin()
@auth.login_required
def getModelExperiments():
    page_size = 10
    page = request.args.get("page", 1, type=int)
    name = request.args.get("name", "")
    user_name = request.args.get("user_key", "")

    exps = mlflow_client.list_experiments()
    total_pages = 1

    response_message = ListExperiments.Response()
    response_message.experiments.extend([e.to_proto() for e in exps])

    data = json.loads(message_to_json(response_message))
    if len(data) > 0:
        _data = data["experiments"]
    else:
        _data = []
    result = {"data": _data, "page": page, "total": total_pages}
    return rsp.success(result)


@app.route("/api/experiments/add_model_experiment", methods=["POST"])
@cross_origin()
@auth.login_required
def add_model_experiment():
    try:
        experiment_name = request.get_json()["name"]
        tag = request.get_json().get("tag", None)
        user_name = request.get_json()["user"]
        artifact_location = request.get_json().get("artifact_location", None)
        exp = mlflow_client.get_experiment_by_name(experiment_name)
        if exp is not None:
            return rsp.failed("模型项目{}已经存在".format(experiment_name))
        experiment_id = mlflow_client.create_experiment(
            experiment_name, artifact_location=artifact_location
        )
        if tag is None:
            return rsp.success("model experiment added success!")
        mlflow_client.set_experiment_tag(str(experiment_id), "model_experiment", tag)
        return rsp.success("model experiment added success!")
    except:
        exc_traceback = str(traceback.format_exc())
        return rsp.failed(exc_traceback)


@app.route("/api/models/get_registered_models", methods=["GET"])
@cross_origin()
@auth.login_required
def getRegisteredModels():
    import json

    page = request.args.get("page", 1, type=int)
    name = request.args.get("name", "")
    user_name = request.args.get("user_key", "")

    models = mlflow_client.list_registered_models()
    total_pages = 1

    response_message = ListRegisteredModels.Response()
    response_message.registered_models.extend([m.to_proto() for m in models])

    data = json.loads(message_to_json(response_message))
    registered_models = []
    # with open("/Users/leepand/Downloads/codes/mlops-test/modelinfo.json", "w") as f:
    #    json.dump(data, f)
    model_meta = {}
    if data:
        for model in data["registered_models"]:
            model_new_dict = {}
            model_new_dict["name"] = model["name"]
            model_new_dict["creation_timestamp"] = model["creation_timestamp"]
            model_new_dict["last_updated_timestamp"] = model["last_updated_timestamp"]
            model_new_dict["description"] = model.get("description", "无")
            model_new_dict["tags"] = model.get("tags", [])

            with sfdb.Database(filename=model_meta_file) as db:
                _name = model["name"]
                model_key = f"{_name}:port"
                modelservice = db.get(model_key)
                if modelservice is not None:
                    model_meta[_name] = modelservice
                else:
                    model_meta[_name] = {
                        "name": _name,
                        "port": "null",
                        "status": "stoped",
                    }
                    db[model_key] = model_meta[_name]

            if "latest_versions" in model:
                model_new_dict["latest_version"] = model["latest_versions"][-1][
                    "version"
                ]
                for latest_version in model["latest_versions"]:
                    if latest_version["current_stage"] == "Production":
                        model_new_dict["latest_version_prodcution"] = latest_version[
                            "version"
                        ]
                        break
            else:
                model_new_dict["latest_version_prodcution"] = ""
                model_new_dict["latest_version"] = ""

            registered_models.append(model_new_dict)

    result = {
        "data": registered_models,
        "page": page,
        "total": total_pages,
        "model_meta": model_meta,
    }
    return rsp.success(result)


@app.route("/api/models/check_service_status", methods=["POST"])
@cross_origin()
@auth.login_required
def check_service_status():
    try:
        model_name = request.get_json()["model_name"]
        ifall = request.get_json().get("ifall")
        user_name = request.get_json()["user_name"]
        print(ifall, model_name, "sfsf")
        if ifall == "no":
            with sfdb.Database(filename=model_meta_file) as db:
                _name = model_name
                model_key = f"{_name}:port"
                modelservice = db.get(model_key)
                modelservice["model_name"] = model_name
                port = modelservice["port"]
                if port == "null":
                    return rsp.success({"model_meta": modelservice, "ifall": "no"})
                fd_pid = os.popen("lsof -i:%s|awk '{print $2}'" % str(port))
                pids = fd_pid.read().strip().split("\n")
                db["model_name"] = model_name

                if len(pids) > 1:
                    modelservice["status"] = "running"
                    db[model_key] = modelservice
                else:
                    modelservice["status"] = "stoped"
                    db[model_key] = modelservice
            print(modelservice, "modelservice")
            return rsp.success({"model_meta": modelservice, "ifall": "no"})
        else:
            models = mlflow_client.list_registered_models()
            response_message = ListRegisteredModels.Response()
            response_message.registered_models.extend([m.to_proto() for m in models])

            data = json.loads(message_to_json(response_message))
            registered_models = []
            if data:
                model_meta = {}
                for model in data["registered_models"]:
                    model_name = model["name"]
                    with sfdb.Database(filename=model_meta_file) as db:
                        model_key = f"{model_name}:port"
                        modelservice = db.get(model_key)
                        port = modelservice["port"]
                        if port == "null":
                            model_meta[model_name] = modelservice
                        else:
                            fd_pid = os.popen("lsof -i:%s|awk '{print $2}'" % str(port))
                            pids = fd_pid.read().strip().split("\n")
                            if len(pids) > 1:
                                modelservice["status"] = "running"
                                db[model_key] = modelservice
                                model_meta[model_name] = modelservice
                            else:
                                modelservice["status"] = "stoped"
                                db[model_key] = modelservice
                                model_meta[model_name] = modelservice
                return rsp.success({"model_meta": model_meta, "ifall": "yes"})

    except:
        exc_traceback = str(traceback.format_exc())
        return rsp.failed(exc_traceback)


@app.route("/api/models/register_model", methods=["POST"])
@cross_origin()
@auth.login_required
def register_model():
    try:
        model_name = request.get_json()["model_name"]
        description = request.get_json().get("description", None)
        user_name = request.get_json()["user_name"]
        try:
            registered_model = mlflow_client.get_registered_model(model_name)
        except:
            registered_model = None
        if registered_model is not None:
            return rsp.failed("模型{}已经存在".format(model_name))
        mlflow_client.create_registered_model(
            model_name, description=description, tags={"author": user_name}
        )
        return rsp.success("model added success!")
    except:
        exc_traceback = str(traceback.format_exc())
        return rsp.failed(exc_traceback)


@app.route("/api/models/get_model_base_info", methods=["GET"])
@cross_origin()
@auth.login_required
def get_model_base_info():
    name = request.args.get("name", "")
    user_name = request.args.get("user_key", "")

    registered_model = mlflow_client.get_registered_model(name=name)
    response_message = GetRegisteredModel.Response(
        registered_model=registered_model.to_proto()
    )
    data = json.loads(message_to_json(response_message))
    result = data["registered_model"]
    meta_info = {}
    meta_info["name"] = result.get("name", "无")
    meta_info["description"] = result.get("description", "无")
    meta_info["creation_timestamp"] = result.get("creation_timestamp")
    meta_info["last_updated_timestamp"] = result.get("last_updated_timestamp")
    meta_info["tags"] = result.get("tags", [])
    return rsp.success(meta_info)


@app.route("/api/models/edit_model_description", methods=["POST"])
@cross_origin()
@auth.login_required
def edit_model_description():
    try:
        model_name = request.get_json()["model_name"]
        description = request.get_json().get("description", None)
        user_name = request.get_json()["user_name"]

        mlflow_client.update_registered_model(name=model_name, description=description)

        return rsp.success("model desc edit success!")
    except:
        exc_traceback = str(traceback.format_exc())
        return rsp.failed(exc_traceback)


@app.route("/api/models/get_model_versions", methods=["GET"])
@cross_origin()
@auth.login_required
def get_model_versions():
    name = request.args.get("name", "")
    page = request.args.get("page", 1)
    user_name = request.args.get("user_key", "")
    stage_btn = request.args.get("stage_btn", "all")

    if stage_btn == "active":
        stages = ["Production", "Staging"]
        latest_versions = mlflow_client.get_latest_versions(name=name, stages=stages)
        response_message = GetLatestVersions.Response()
        response_message.model_versions.extend([e.to_proto() for e in latest_versions])
    else:
        filter_string = "name='{0}'".format(name)
        model_versions = mlflow_client.search_model_versions(filter_string)
        response_message = SearchModelVersions.Response()
        response_message.model_versions.extend([e.to_proto() for e in model_versions])

    json_data = json.loads(message_to_json(response_message))

    data = json_data.get("model_versions", [])
    result = {"data": data, "page": page, "total": 1}

    return rsp.success(result)


@app.route("/api/models/get_model_base_versioninfo", methods=["GET"])
@cross_origin()
@auth.login_required
def get_model_base_versioninfo():
    name = request.args.get("name", "")
    version = request.args.get("version", "")
    user_name = request.args.get("user_key", "")
    model_version = mlflow_client.get_model_version(name=name, version=version)
    response_proto = model_version.to_proto()
    response_message = GetModelVersion.Response(model_version=response_proto)

    json_data = json.loads(message_to_json(response_message))

    result = json_data.get("model_version", {})

    return rsp.success(result)


@app.route("/api/models/model_stage_transform", methods=["POST"])
@cross_origin()
@auth.login_required
def model_stage_transform():
    try:
        model_name = request.get_json()["model_name"]
        version = request.get_json().get("version", "1")
        user_name = request.get_json()["user_name"]
        stage = request.get_json()["stage"]
        print(stage, model_name, version, "fdff")
        model_version = mlflow_client.transition_model_version_stage(
            name=model_name, version=version, stage=stage
        )

        return rsp.success("model stage transform success!")
    except:
        exc_traceback = str(traceback.format_exc())
        return rsp.failed(exc_traceback)


@app.route("/api/models/edit_model_version_description", methods=["POST"])
@cross_origin()
@auth.login_required
def edit_model_version_description():
    try:
        model_name = request.get_json()["model_name"]
        version = request.get_json()["version"]
        description = request.get_json().get("description", None)
        user_name = request.get_json()["user_name"]

        mlflow_client.update_model_version(
            name=model_name, version=version, description=description
        )

        return rsp.success("model model version desc edit success!")
    except:
        exc_traceback = str(traceback.format_exc())
        return rsp.failed(exc_traceback)


@app.route("/api/experiments/get_model_experiment", methods=["GET"])
@cross_origin()
@auth.login_required
def get_model_experiment():
    experiment_id = request.args.get("experiment_id", "")
    user_name = request.args.get("user_name", "")

    response_message = GetExperiment.Response()
    experiment = mlflow_client.get_experiment(experiment_id).to_proto()
    response_message.experiment.MergeFrom(experiment)

    json_data = json.loads(message_to_json(response_message))
    result = json_data.get("experiment", {})
    tags = result.get("tags", [{"key": "mlops.framework", "value": "无"}])
    result["tags"] = tags
    return rsp.success(result)


@app.route("/api/experiments/edit_experiment_description", methods=["POST"])
@cross_origin()
@auth.login_required
def edit_experiment_description():
    try:
        experiment_id = request.get_json().get("experiment_id")
        description = request.get_json().get("description", None)
        user_name = request.get_json()["user_name"]

        mlflow_client.set_experiment_tag(experiment_id, "mlops.framework", description)

        return rsp.success("model experiment desc edit success!")
    except:
        exc_traceback = str(traceback.format_exc())
        return rsp.failed(exc_traceback)


@app.route("/api/experiments/get_model_runs", methods=["GET"])
@cross_origin()
@auth.login_required
def get_model_runs():
    experiment_id = request.args.get("experiment_id", "")
    user_name = request.args.get("user_name", "")

    experiment_ids = [experiment_id]
    run_entities = mlflow_client.search_runs(
        experiment_ids, filter_string="", max_results=1000, order_by=None
    )
    response_message = SearchRuns.Response()
    response_message.runs.extend([r.to_proto() for r in run_entities])
    json_data = json.loads(message_to_json(response_message))
    result = json_data.get("runs", [])
    return rsp.success(result)


@app.route("/api/experiments/get_model_run", methods=["GET"])
@cross_origin()
@auth.login_required
def get_model_run():
    run_id = request.args.get("run_id", "")
    user_name = request.args.get("user_name", "")

    response_message = GetRun.Response()
    # run_id = '7033fe2d709848d585683c6b3fd45be7'
    response_message.run.MergeFrom(mlflow_client.get_run(run_id).to_proto())
    json_data = json.loads(message_to_json(response_message))
    result = json_data.get("run", {})
    data = result.get("data", {})
    if len(data) < 1:
        result["tags"] = [{"key": "mlops.framework", "value": "无"}]
    else:
        tags = data.get("tags", [{"key": "mlops.framework", "value": "无"}])
        result["tags"] = tags
    return rsp.success(result)


def get_model_monitor_db(name, version):
    model_version = mlflow_client.get_model_version(name=name, version=version)
    response_proto = model_version.to_proto()
    response_message = GetModelVersion.Response(model_version=response_proto)

    json_data = json.loads(message_to_json(response_message))

    result = json_data.get("model_version", {})
    # get model deploy path
    dir_name = os.path.dirname(result.get("source", ""))
    db_file = os.path.join(mlops_art_basepath, dir_name, "sqlite_logs.db")
    # print(db_file, "db_file")
    defa_db_uri = path_to_local_sqlite_uri(db_file)
    new_sql_db = MonitorModelInit(defa_db_uri)
    return new_sql_db


@app.route("/api/models/get_model_monitorinfo", methods=["GET"])
@cross_origin()
@auth.login_required
def get_model_monitorinfo():
    model_name = request.args.get("name", "")
    version_id = request.args.get("version_id", "")
    new_sql_db = get_model_monitor_db(model_name, version_id)
    table_name = "predictions"
    new_sql_db = get_model_monitor_file(model_name, version_id)
    initialize_app(new_sql_db)
    # with new_sql_db._session() as s:
    #    q_all = s.query(SPrediction).filter(SPrediction.id > 0)
    #    q_errors = s.query(SPrediction).filter(SPrediction.log_type == "errors")
    #    data_all = [serialize(o.to_obj()) for o in q_all.all()]
    #    data_errors = [serialize(o.to_obj()) for o in q_errors.all()]
    data = []
    sql = "select count(*) as cnt,log_type from predictions group by log_type"
    try:
        cursor = dataset.query(sql)
    except Exception as exc:
        error = str(exc)
    else:
        # total_rows = len(cursor.fetchall())

        # total_pages = int(math.ceil(total_rows / float(rows_per_page)))
        # Restrict bounds.
        # page_number = min(page_number, total_pages)
        # page_number = max(page_number, 1)

        # previous_page = page_number - 1 if page_number > 1 else None
        # next_page = page_number + 1 if page_number < total_pages else None

        data = cursor.fetchall()[:10000]
    all_predict_cnt = 0
    errors_cnt = 0
    if len(data) > 0:
        for cnt, log_type in data:
            all_predict_cnt += cnt
            if log_type == "errors":
                errors_cnt += cnt
    # print(data,"datasql")
    # result = {"all_predict_cnt": len(data_all), "errors_cnt": len(data_errors)}
    result = {"all_predict_cnt": all_predict_cnt, "errors_cnt": errors_cnt}
    return rsp.success(result)


@app.route("/api/models/get_predictions", methods=["GET"])
@cross_origin()
@auth.login_required
def get_predictions():
    model_name = request.args.get("name", "")
    version_id = request.args.get("version_id", "")
    user_name = request.args.get("user_name", "")
    page_pred = request.args.get("page_pred", "")
    process_btn = request.args.get("process_btn", "all")
    page_size = 10
    # source = mlflow_client.get_model_version_download_url(model_name, model_version)
    # (path, filename) = os.path.split(source)
    # db_file = os.path.join(mlops_art_basepath, path, "sqlite_logs.db")
    # with open("/Users/leepand/Downloads/codes/mlops-test/path.txt","w") as f:
    #    f.write(os.path.join( mlops_art_basepath, dir_name,path))

    # data_store = SQLDataStore(path_to_local_sqlite_uri(db_file))
    # data_store.build()
    new_sql_db = get_model_monitor_db(model_name, version_id)

    with new_sql_db._session() as s:
        if process_btn == "all":
            q = s.query(SPrediction).filter(SPrediction.id > 0)
        else:
            q = s.query(SPrediction).filter(SPrediction.log_type == "errors")
        paginator = Paginator(q, page_size)
        _page = paginator.page(page_pred)
        total_pages = _page.paginator.total_pages
        data = [serialize(o.to_obj()) for o in _page.object_list]

    result = {"data": data, "page": page_pred, "total": total_pages}
    return rsp.success(result)


@app.route("/api/experiments/edit_modelrun_description", methods=["POST"])
@cross_origin()
@auth.login_required
def edit_modelrun_description():
    try:
        run_id = request.get_json().get("run_id")
        description = request.get_json().get("description", None)
        user_name = request.get_json()["user_name"]

        mlflow_client.set_tag(run_id, "mlops.framework", description)

        return rsp.success("model run desc edit success!")
    except:
        exc_traceback = str(traceback.format_exc())
        return rsp.failed(exc_traceback)


@app.route("/api/models/get_models_markdown", methods=["POST"])
@cross_origin()
@auth.login_required
def get_models_markdown():
    model_name = request.get_json()["model_name"]
    version_id = request.get_json()["version_id"]
    model_version = mlflow_client.get_model_version(name=model_name, version=version_id)
    response_proto = model_version.to_proto()
    response_message = GetModelVersion.Response(model_version=response_proto)

    json_data = json.loads(message_to_json(response_message))

    result = json_data.get("model_version", {})
    dir_name = os.path.dirname(result.get("source", ""))
    model_jupyter_path = os.path.join(mlops_art_basepath, dir_name)
    print(model_jupyter_path, "model_jupyter_path")

    files = []

    def find_jupyter_files(directory_files, exclude=[]):
        for file in os.scandir(directory_files):
            if file.name in exclude:
                continue
            if file.is_dir():
                find_jupyter_files(file.path)
            else:
                fname = file.name
                # print(fname)
                if fname.endswith(".ipynb"):
                    files.append({fname: file.path})
        return files

    _fnamePath = ""
    jupyterFile_list = find_jupyter_files(model_jupyter_path)
    to_html_filename = None
    for jupyterFile_dict in jupyterFile_list:
        filename = list(jupyterFile_dict.keys())[0]
        filepath = jupyterFile_dict[filename]
        _dir_name = os.path.dirname(filepath)
        _filename = filename.split(".")[0]
        to_html_filename = os.path.join(_dir_name, ".".join([_filename, "html"]))
        if os.path.exists(to_html_filename):
            continue
        file1 = open(filepath, "r+")
        file_content = file1.read()
        print("Output of Read function is ")
        print(type(file1.read()))
        file1.close()
        jake_notebook = nbformat.reads(file_content, as_version=4)
        # 2. Instantiate the exporter. We use the `classic` template for now; we'll get into more details
        #  later about how to customize the exporter further.
        html_exporter = HTMLExporter()
        html_exporter.template_name = "classic"

        # 3. Process the notebook we loaded earlier
        (body, resources) = html_exporter.from_notebook_node(jake_notebook)
        # in other words, we replace the template tag
        #  by the contents of the overfitting file
        #  write the result to disk in index.html

        try:
            # os.makedirs(htmlpath, exist_ok=True)
            print("Directory '%s' created successfully" % to_html_filename)
        except OSError as error:
            print("Directory '%s' can not be created")

        with open(to_html_filename, "w") as ofile:
            ofile.write(body)

    # file_to_view = os.path.join(filepath,file_to_view)
    if not to_html_filename:
        send_as_attachment = False
        mimetype = "text/plain"
        file_to_view = ""
        return send_file(
            file_to_view, mimetype=mimetype, as_attachment=send_as_attachment
        )
    file_to_view = to_html_filename
    if file_to_view:
        # Check if file extension
        (filename, extension) = os.path.splitext(file_to_view)
        send_as_attachment = False
        if extension == "":
            mimetype = "text/plain"
        else:
            mimetype = None

        return send_file(
            file_to_view, mimetype=mimetype, as_attachment=send_as_attachment
        )


@app.route("/api/modelfile/rename_file_dir_name", methods=["POST"])
@cross_origin()
@auth.login_required
def rename_file_dir_name():
    new_name = request.get_json()["name"]
    old_name = request.get_json()["old_name"]
    file_path = request.get_json()["path"]
    old_path_name = os.path.join(file_path, old_name)
    new_path_name = os.path.join(file_path, new_name)

    os.rename(old_path_name, new_path_name)
    return rsp.success("ok")


@app.route("/api/modelfile/del_file_dir", methods=["POST"])
@cross_origin()
@auth.login_required
def del_file_dir():
    del_name = request.get_json()["name"]
    file_path = request.get_json()["path"]
    tobeDelFileDirType = request.get_json()["tobeDelFileDirType"]
    file_or_path = os.path.join(file_path, del_name)
    if tobeDelFileDirType == "dir":
        del_file(file_or_path)
    else:
        try:
            os.remove(file_or_path)
        except:
            rsp.failed("no file or Permission Denied")

    return rsp.success("ok")


@app.route("/api/models/get_model_files", methods=["GET"])
@cross_origin()
@auth.login_required
def get_model_files():
    page_size = 10
    page = request.args.get("page", 1, type=int)
    _path = request.args.get("path", None)
    is_dir = request.args.get("is_dir", None)
    model_name = request.args.get("model_name")
    version_id = request.args.get("version_id")
    handle_cat = request.args.get("p_type")
    print(is_dir, type(is_dir), "isdir")
    p_type = handle_cat
    if is_dir:
        path = _path
    else:
        path = os.path.basename(_path)

    # path = "/".join(_path.split("/")[2:-1])
    model_version = mlflow_client.get_model_version(name=model_name, version=version_id)
    response_proto = model_version.to_proto()
    response_message = GetModelVersion.Response(model_version=response_proto)

    json_data = json.loads(message_to_json(response_message))

    result = json_data.get("model_version", {})
    # get model deploy path
    dir_name = os.path.dirname(result.get("source", ""))
    # with open("/Users/leepand/Downloads/codes/mlops-test/path.txt","w") as f:
    #    f.write(os.path.join( mlops_art_basepath, dir_name,path))

    model_version_files_path = os.path.join(mlops_art_basepath, dir_name)

    global base_directory
    base_directory = model_version_files_path
    # If there is a path parameter and it is valid
    if path and is_valid_subpath(path, base_directory):
        # Take off the trailing '/'
        path = os.path.normpath(path)
        requested_path = os.path.join(base_directory, path)
        # with open("/Users/leepand/Downloads/codes/mlops-test/requested_path.txt","w") as f:
        #    f.write(requested_path)
        print(requested_path, "requested_path")
        # If directory
        if os.path.isdir(requested_path):
            # back = os.path.dirname(requested_path)#get_parent_directory(requested_path, base_directory)
            back = get_parent_directory(requested_path, base_directory)
            # back=back.split("/")[-1]
            is_subdirectory = True

        # If file
        elif os.path.isfile(requested_path):

            # Check if the view flag is set
            if request.args.get("view") is None:
                send_as_attachment = True
            else:
                send_as_attachment = False

            # Check if file extension
            (filename, extension) = os.path.splitext(requested_path)
            if extension == "":
                mimetype = "text/plain"
            else:
                mimetype = None
            print(send_as_attachment, requested_path, "requested_pathddd")
            try:
                print(send_as_attachment, requested_path, "requested_path")
                return send_file(
                    requested_path, mimetype=mimetype, as_attachment=send_as_attachment
                )
            except PermissionError:
                rsp.failed("Read Permission Denied: " + requested_path)
    else:
        # Root home configuration
        is_subdirectory = False
        requested_path = base_directory
        back = ""
    # print(os.path.exists(requested_path),requested_path,"os.path.exists(requested_path)")
    if os.path.exists(requested_path):
        # Read the files
        try:
            exclude = ["venv"]
            directory_files = process_files(
                os.scandir(requested_path),
                base_directory,
                exclude=exclude,
                p_type=p_type,
            )
        except PermissionError:
            rsp.failed("Read Permission Denied: " + requested_path)

        result = {
            "files": directory_files,
            "back": back,
            "directory": requested_path,
            "is_subdirectory": is_subdirectory,
            "page": 1,
            "total": 1,
            "version": "v1.0",
        }
        print(result, "model_results")
        return rsp.success(result)
    else:
        os.makedirs(requested_path, exist_ok=True)
        result = {
            "files": [],
            "back": "",
            "directory": requested_path,
            "is_subdirectory": False,
            "page": 1,
            "total": 1,
            "version": "v1.0",
        }
        return rsp.success(result)


@app.route("/api/models/cat_file_contents", methods=["POST"])
@cross_origin()
@auth.login_required
def cat_file_contents():
    model_name = request.get_json()["model_name"]
    version_id = request.get_json()["version_id"]
    curr_path = request.get_json()["path"]
    filename = request.get_json()["filename"]
    is_subdirectory = request.get_json()["is_subdirectory"]
    path = os.path.basename(curr_path)

    # path = "/".join(_path.split("/")[2:-1])
    model_version = mlflow_client.get_model_version(name=model_name, version=version_id)
    response_proto = model_version.to_proto()
    response_message = GetModelVersion.Response(model_version=response_proto)

    json_data = json.loads(message_to_json(response_message))

    result = json_data.get("model_version", {})
    # get model deploy path
    dir_name = os.path.dirname(result.get("source", ""))
    # with open("/Users/leepand/Downloads/codes/mlops-test/path.txt","w") as f:
    #    f.write(os.path.join( mlops_art_basepath, dir_name,path))

    model_version_files_path = os.path.join(mlops_art_basepath, dir_name)

    global base_directory
    base_directory = model_version_files_path
    # If there is a path parameter and it is valid
    # is_subdirectory = False
    _requested_path = os.path.join(base_directory, curr_path)
    (requested_path, _filename) = os.path.split(_requested_path)
    back = requested_path
    try:
        file_content = cat_file_content(_requested_path, _filename)
    except PermissionError:
        rsp.failed("Read Permission Denied: " + requested_path)
    if back == base_directory:
        back = ""
    result = {
        "file_content": file_content,
        "back": back,
        "directory": requested_path,
        "is_subdirectory": is_subdirectory,
        "is_dir": False,
        "page": 1,
        "total": 1,
        "version": "v1.0",
    }
    # print(result,"result")
    return rsp.success(result)


@app.route("/api/models/upload_model_files", methods=["POST"])
@cross_origin()
@auth.login_required
def upload_model_files():
    file_obj = request.files.get("file")
    # files= request.files.getlist('file')
    # base_directory
    # No file part - needs to check before accessing the files['file']
    if "file" not in request.files:
        return rsp.failed("No file part")

    path = request.form["pathParam"]
    # Prevent file upload to paths outside of base directory
    # if not is_valid_upload_path(path, base_directory):
    #    return rsp.failed("paths outside of base directory")
    # No filename attached
    if file_obj.filename == "":
        return rsp.failed("No filename attached")

    # Assuming all is good, process and save out the file
    # TODO:
    # - Add support for overwriting
    print(file_obj, "file_objfile_obj")
    if file_obj:
        filename = secure_filename(file_obj.filename)
        full_path = os.path.join(path, filename)
        print(full_path, "full_path")
        try:
            file_obj.save(full_path)
        except PermissionError:
            rsp.failed("Write Permission Denied: " + full_path)
    print(path, file_obj, "file_obj")

    return rsp.success("upload sucess")


from peewee import *
from peewee import IndexMetadata
from peewee import sqlite3
from playhouse.dataset import DataSet
from playhouse.migrate import migrate
from collections import namedtuple, OrderedDict

try:
    from pygments import formatters, highlight, lexers
except ImportError:
    import warnings

    warnings.warn("pygments library not found.", ImportWarning)
    syntax_highlight = lambda data: "<pre>%s</pre>" % data
else:

    def syntax_highlight(data):
        if not data:
            return ""
        lexer = lexers.get_lexer_by_name("sql")
        formatter = formatters.HtmlFormatter(linenos=False)
        return highlight(data, lexer, formatter)


dataset = None
migrator = None

#
# Database metadata objects.
#

TriggerMetadata = namedtuple("TriggerMetadata", ("name", "sql"))

ViewMetadata = namedtuple("ViewMetadata", ("name", "sql"))


class SqliteDataSet(DataSet):
    @property
    def filename(self):
        db_file = dataset._database.database
        if db_file.startswith("file:"):
            db_file = db_file[5:]
        return os.path.realpath(db_file.rsplit("?", 1)[0])

    @property
    def is_readonly(self):
        db_file = dataset._database.database
        return db_file.endswith("?mode=ro")

    @property
    def base_name(self):
        return os.path.basename(self.filename)

    @property
    def created(self):
        stat = os.stat(self.filename)
        return datetime.datetime.fromtimestamp(stat.st_ctime)

    @property
    def modified(self):
        stat = os.stat(self.filename)
        return datetime.datetime.fromtimestamp(stat.st_mtime)

    @property
    def size_on_disk(self):
        stat = os.stat(self.filename)
        return stat.st_size

    def get_indexes(self, table):
        return dataset._database.get_indexes(table)

    def get_all_indexes(self):
        cursor = self.query(
            "SELECT name, sql FROM sqlite_master " "WHERE type = ? ORDER BY name",
            ("index",),
        )
        return [
            IndexMetadata(row[0], row[1], None, None, None) for row in cursor.fetchall()
        ]

    def get_columns(self, table):
        return dataset._database.get_columns(table)

    def get_foreign_keys(self, table):
        return dataset._database.get_foreign_keys(table)

    def get_triggers(self, table):
        cursor = self.query(
            "SELECT name, sql FROM sqlite_master " "WHERE type = ? AND tbl_name = ?",
            ("trigger", table),
        )
        return [TriggerMetadata(*row) for row in cursor.fetchall()]

    def get_all_triggers(self):
        cursor = self.query(
            "SELECT name, sql FROM sqlite_master " "WHERE type = ? ORDER BY name",
            ("trigger",),
        )
        return [TriggerMetadata(*row) for row in cursor.fetchall()]

    def get_all_views(self):
        cursor = self.query(
            "SELECT name, sql FROM sqlite_master " "WHERE type = ? ORDER BY name",
            ("view",),
        )
        return [ViewMetadata(*row) for row in cursor.fetchall()]

    def get_virtual_tables(self):
        cursor = self.query(
            "SELECT name FROM sqlite_master "
            "WHERE type = ? AND sql LIKE ? "
            "ORDER BY name",
            ("table", "CREATE VIRTUAL TABLE%"),
        )
        return set([row[0] for row in cursor.fetchall()])

    def get_corollary_virtual_tables(self):
        virtual_tables = self.get_virtual_tables()
        suffixes = ["content", "docsize", "segdir", "segments", "stat"]
        return set(
            "%s_%s" % (virtual_table, suffix)
            for suffix in suffixes
            for virtual_table in virtual_tables
        )


def initialize_app(filename, read_only=False, password=None, url_prefix=None):
    global dataset
    global migrator

    if password:
        install_auth_handler(password)

    if read_only:
        if sys.version_info < (3, 4, 0):
            die("Python 3.4.0 or newer is required for read-only access.")
        if peewee_version < (3, 5, 1):
            die("Peewee 3.5.1 or newer is required for read-only access.")
        db = SqliteDatabase("file:%s?mode=ro" % filename, uri=True)
        try:
            db.connect()
        except OperationalError:
            die(
                "Unable to open database file in read-only mode. Ensure that "
                "the database exists in order to use read-only mode."
            )
        db.close()
        dataset = SqliteDataSet(db, bare_fields=True)
    else:
        dataset = SqliteDataSet("sqlite:///%s" % filename, bare_fields=True)

    if url_prefix:
        app.wsgi_app = PrefixMiddleware(app.wsgi_app, prefix=url_prefix)

    migrator = dataset._migrator
    dataset.close()


import re

column_re = re.compile("(.+?)\((.+)\)", re.S)
column_split_re = re.compile(r"(?:[^,(]|\([^)]*\))+")


def _format_create_table(sql):
    create_table, column_list = column_re.search(sql).groups()
    columns = [
        "  %s" % column.strip()
        for column in column_split_re.findall(column_list)
        if column.strip()
    ]
    return "%s (\n%s\n)" % (create_table, ",\n".join(columns))


def highlight_filter(data):
    return Markup(syntax_highlight(data))


def format_index(index_sql):
    split_regex = re.compile(r"\bon\b", re.I)
    if not split_regex.search(index_sql):
        return index_sql

    create, definition = split_regex.split(index_sql)
    return "\nON ".join((create.strip(), definition.strip()))


def export(table, sql, export_format):
    model_class = dataset[table].model_class
    query = model_class.raw(sql).dicts()
    buf = StringIO()
    if export_format == "json":
        kwargs = {"indent": 2}
        filename = "%s-export.json" % table
        mimetype = "text/javascript"
    else:
        kwargs = {}
        filename = "%s-export.csv" % table
        mimetype = "text/csv"

    dataset.freeze(query, export_format, file_obj=buf, **kwargs)

    response_data = buf.getvalue()
    response = make_response(response_data)
    response.headers["Content-Length"] = len(response_data)
    response.headers["Content-Type"] = mimetype
    response.headers["Content-Disposition"] = "attachment; filename=%s" % (filename)
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "public"
    return response


def get_model_monitor_file(name, version):
    model_version = mlflow_client.get_model_version(name=name, version=version)
    response_proto = model_version.to_proto()
    response_message = GetModelVersion.Response(model_version=response_proto)

    json_data = json.loads(message_to_json(response_message))

    result = json_data.get("model_version", {})
    # get model deploy path
    dir_name = os.path.dirname(result.get("source", ""))
    db_file = os.path.join(mlops_art_basepath, dir_name, "sqlite_logs.db")
    # print(db_file, "db_file")
    # defa_db_uri = path_to_local_sqlite_uri(db_file)
    # new_sql_db = SysModelInit(defa_db_uri)
    return db_file


@app.route("/api/sql/sql_script_excute", methods=["POST"])
@cross_origin()
@auth.login_required
def sql_script_excute():
    model_name = request.get_json()["model_name"]
    version_id = request.get_json()["version_id"]
    table_name = request.get_json()["table_name"]
    if table_name:
        table_name = table_name
    else:
        table_name = "predictions"
    new_sql_db = get_model_monitor_file(model_name, version_id)
    initialize_app(new_sql_db)
    table = table_name

    MAX_RESULT_SIZE = 1000

    sqlScript = request.get_json()["sqlScript"]
    page = request.get_json()["page"]
    export_json = request.get_json()["exportJson"]
    export_csv = request.get_json()["exportCsv"]

    page_number = int(page)
    rows_per_page = 100

    data = []
    data_description = error = row_count = sql = None
    sql = sqlScript

    if export_json:
        print(export(table, sql, "json"), "dddd")
        data = export(table, sql, "json")
        result = {"data": data, "downloadtype": "export_json"}
        # return rsp.success(result)
        return data
    elif export_csv:
        return export(table, sql, "csv")

    try:
        cursor = dataset.query(sql)
    except Exception as exc:
        error = str(exc)
    else:
        # total_rows = len(cursor.fetchall())

        # total_pages = int(math.ceil(total_rows / float(rows_per_page)))
        # Restrict bounds.
        # page_number = min(page_number, total_pages)
        # page_number = max(page_number, 1)

        # previous_page = page_number - 1 if page_number > 1 else None
        # next_page = page_number + 1 if page_number < total_pages else None

        data = cursor.fetchall()[:MAX_RESULT_SIZE]

        data_description = cursor.description
        row_count = cursor.rowcount

    # table_sql = dataset.query(
    #    'SELECT sql FROM sqlite_master WHERE tbl_name = ? AND type = ?',
    #    [table, 'table']).fetchone()[0]
    tableHeader = []
    columns = dataset.get_columns(table)
    column_names = [column.name for column in columns]
    result = {
        "tableData": data,
        "page": page_number,
        "query_data_len": len(data),
        "tableHeader": data_description,
        "defaultSql": sql,
    }
    print(data_description, data, row_count, error, new_sql_db, "select")
    return rsp.success(result)


try:
    from pygments import formatters, highlight, lexers
except ImportError:
    import warnings
from pygments.styles import get_style_by_name

lexer = lexers.get_lexer_by_name("sql")
# style = get_style_by_name("native")
style = get_style_by_name("colorful")
formatter = formatters.HtmlFormatter(linenos=False, full=True, style=style)


@app.route("/api/sql/table_structure", methods=["GET"])
@cross_origin()
@auth.login_required
def table_structure():
    version_id = request.args.get("version_id")
    model_name = request.args.get("model_name")
    table_name = request.args.get("table_name", "")
    # table_name = "predictions"
    db_init = get_model_monitor_db(model_name, version_id)
    new_sql_db = get_model_monitor_file(model_name, version_id)
    initialize_app(new_sql_db)

    table = table_name

    ds_table = dataset[table]
    model_class = ds_table.model_class

    table_sql = dataset.query(
        "SELECT sql FROM sqlite_master WHERE tbl_name = ? AND type = ?",
        [table, "table"],
    ).fetchone()[0]
    columns = dataset.get_columns(table)
    indexes = dataset.get_indexes(table)
    _table_sql = _format_create_table(table_sql)
    # _table_sql = highlight_filter(_table_sql)
    _table_sql = highlight(_table_sql, lexer, formatter)
    sql = 'SELECT *\nFROM "%s" limit 10' % (table)
    tableHeader = []
    for col in columns:
        tableHeader.append(col.name)

    tables = dataset.tables
    result = {
        "data": _table_sql,
        "tables": tables,
        "columns": columns,
        "tableHeader": tableHeader,
        "indexes": indexes,
        "tableName": table_name,
        "defaultSql": format_index(sql),
    }
    print(tables, "table_sql")
    return rsp.success(result)


@app.route("/api/models/format_sql_script", methods=["POST"])
@cross_origin()
@auth.login_required
def format_sql_script():
    model_name = request.get_json()["model_name"]
    version_id = request.get_json()["version_id"]
    sql_script = request.get_json()["sql_script"]
    formatedsql = format_sql(sql_script)

    result = {"formatedsql": formatedsql}

    return rsp.success(result)


@app.route("/api/sql/drop_table", methods=["POST"])
@cross_origin()
@auth.login_required
def drop_table():
    version_id = request.get_json()["version_id"]
    model_name = request.get_json()["model_name"]
    table_name = request.get_json()["table_name"]
    # table_name = "predictions"
    new_sql_db = get_model_monitor_file(model_name, version_id)
    initialize_app(new_sql_db)
    table = table_name
    model_class = dataset[table].model_class
    # model_class.drop_table()
    model_class.truncate_table()
    dataset.update_cache()  # Update all tables.

    return rsp.success("del table success")


@app.route("/api/models/save_sql_script", methods=["POST"])
@cross_origin()
@auth.login_required
def save_sql_script():
    # try:
    model_name = request.get_json()["model_name"]
    version_id = request.get_json().get("version_id")
    sql_name = request.get_json().get("name")
    sql_script = request.get_json().get("sql_script")
    _new_sql_db = get_model_monitor_db(model_name, version_id)
    # print(sql_script,type(sql_script),sql_name,"sfsff")
    # print("sdfsdfsdfssffsfsff")
    obj = SInquiries(
        name=str(sql_name),
        sqlscript=format_sql(sql_script),
        created_at=datetime.datetime.utcnow(),
    )
    # print(obj,"obj")
    _new_sql_db._create_object(obj)
    print(_new_sql_db, "new_sql_db")
    return rsp.success("sql script saved success!")
    # except:
    #    exc_traceback = str(traceback.format_exc())
    #    return rsp.failed(exc_traceback)
