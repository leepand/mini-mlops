# -*- coding: utf-8 -*-
from flask import jsonify, request
from .. import app, auth, sql_db
from flask_cors import cross_origin
import datetime

from pyjackson import deserialize, serialize
from ..models.models import SUsers


from .response import Response

rsp = Response()


# 获取成员信息
@app.route("/api/users/get_user_metadata", methods=["GET"])
@cross_origin()
@auth.login_required
def get_user_meta():
    user_name = request.args.get("user_key", "")
    print(user_name, "user_name")

    _p = sql_db._get_objects(SUsers, SUsers.name == user_name)
    ab_info = [serialize(o) for o in _p]
    result = {"data": ab_info[0]}
    return rsp.success(result)
