# -*- coding: utf-8 -*-
from flask import jsonify, request
from .. import app, auth, sql_db, mlflow_client
from flask_cors import cross_origin
import datetime

from pyjackson import deserialize, serialize

from ..models.models import SDataCampaign, SAbExpCase, SAbExpOps


from .response import Response

rsp = Response()


# 获取dashboard信息
@app.route("/api/dashboard/get_dashboard_info", methods=["GET"])
@cross_origin()
@auth.login_required
def get_dashboard_info():
    user_name = request.args.get("user_name", "")
    dashboard_all = []
    _p = sql_db._get_objects(SDataCampaign)
    campaign_info = [serialize(o) for o in _p]
    campaign_dict = {"cnt": len(campaign_info), "title": "已建活动数", "link": "/campaigns"}
    dashboard_all.append(campaign_dict)

    _p2 = sql_db._get_objects(SAbExpCase)
    ab_info = [serialize(o) for o in _p2]

    exp_dict = {"cnt": len(ab_info), "title": "进行中的实验数", "link": "/campaigns"}
    dashboard_all.append(exp_dict)

    model_dict = {
        "cnt": len(mlflow_client.list_registered_models()),
        "title": "已注册的模型数",
        "link": "/models",
    }

    dashboard_all.append(model_dict)
    models = mlflow_client.list_registered_models()
    model_versions_cnt = 0
    for model in models:
        name = model.name
        filter_string = "name='{0}'".format(name)
        model_versions = mlflow_client.search_model_versions(filter_string)
        model_versions_cnt += len(model_versions)

    model_v_dict = {"cnt": model_versions_cnt, "title": "模型版本数", "link": "/models"}
    dashboard_all.append(model_v_dict)

    return rsp.success(dashboard_all)
