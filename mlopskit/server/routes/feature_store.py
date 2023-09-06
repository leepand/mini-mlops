from .. import app, auth, sql_db, mlflow_client
from flask import request
from flask_cors import cross_origin
import datetime
import traceback
import os

from mlopskit.utils.file_utils import path_to_local_sqlite_uri
from sqlalchemy_paginator import Paginator
from pyjackson import deserialize, serialize

from .response import Response
from .. import mlops_art_basepath
from ..models.featureinit import FeatureModelInit
from ..models.feature_store import SFeatureBase, SFeatureModel


def get_featuremeta_db():

    db_file = os.path.join(mlops_art_basepath, "feature_meta.db")
    # print(db_file, "db_file")
    defa_db_uri = path_to_local_sqlite_uri(db_file)
    new_sql_db = FeatureModelInit(defa_db_uri)
    return new_sql_db


rsp = Response()

import re
from typing import (
    Optional,
    Tuple,
)
import warnings


class Error(Exception):
    """Error superclass."""


ENV_ID_RE = re.compile(
    r"^(?:(?P<namespace>[\w:-]+)\/)?(?:(?P<name>[\w:.-]+?))(?:-v(?P<version>\d+))?$"
)


def parse_env_id(id: str) -> Tuple[Optional[str], str, Optional[int]]:
    """Parse environment ID string format.
    This format is true today, but it's *not* an official spec.
    [namespace/](env-name)-v(version)    env-name is group 1, version is group 2
    2016-10-31: We're experimentally expanding the environment ID format
    to include an optional namespace.
    Args:
        id: The environment id to parse
    Returns:
        A tuple of environment namespace, environment name and version number
    Raises:
        Error: If the environment id does not a valid environment regex
    """
    match = ENV_ID_RE.fullmatch(id)
    if not match:
        raise Error(
            f"Malformed environment ID: {id}."
            f"(Currently all IDs must be of the form [namespace/](env-name)-v(version). (namespace is optional))"
        )
    namespace, name, version = match.group("namespace", "name", "version")
    if version is not None:
        version = int(version)

    return namespace, name, version


@app.route("/api/features", methods=["GET"])
@cross_origin()
@auth.login_required
def registered_features():
    page = request.args.get("page", 1, type=int)
    name = request.args.get("name", "")
    feature_or_model = request.args.get("feature_or_model", "feature")
    page_size = 10

    new_sql_db = get_featuremeta_db()
    showSearch = False
    searchResultModel = "null"
    model_version = None
    with new_sql_db._session() as s:
        q = s.query(SFeatureBase).filter(SFeatureBase.id > 0)
        if name:
            ns, model_name, model_version = parse_env_id(name)
            print(ns, model_name, model_version)
            if ns in [None, "feature", "id"]:
                if ns is None:
                    # q = q.filter(SFeatureBase.feature_en.ilike("%{}%".format(name)))
                    q1 = s.query(SFeatureBase).filter(
                        SFeatureBase.feature_en.ilike("%{}%".format(name))
                    )
                    q2 = s.query(SFeatureBase).filter(
                        SFeatureBase.feature_cn.ilike("%{}%".format(name))
                    )
                    merged_query = q1.union(q2).distinct()
                    q = merged_query  # .all()
                elif ns == "feature":
                    q = s.query(SFeatureBase).filter(
                        SFeatureBase.feature_cn.ilike("%{}%".format(model_name))
                    )

                else:
                    q = s.query(SFeatureBase).filter(
                        SFeatureBase.feature_en.ilike("%{}%".format(model_name))
                    )

            elif ns == "model" and model_name:
                showSearch = True
                if model_version is None:

                    model_q = (
                        s.query(SFeatureModel.feature_id)
                        .filter(SFeatureModel.name.ilike("%{}%".format(model_name)))
                        .distinct()
                    )
                    model_q_name = (
                        s.query(SFeatureModel.name)
                        .filter(SFeatureModel.name.ilike("%{}%".format(model_name)))
                        .distinct()
                    )
                    q = q.filter(SFeatureBase.id.in_(model_q))

                else:
                    model_q = (
                        s.query(SFeatureModel.feature_id)
                        .filter(
                            SFeatureModel.name.ilike("%{}%".format(model_name)),
                            SFeatureModel.version.ilike("%{}%".format(model_version)),
                        )
                        .distinct()
                    )
                    model_q_name = (
                        s.query(SFeatureModel.name)
                        .filter(SFeatureModel.name.ilike("%{}%".format(model_name)))
                        .distinct()
                    )
                    q = q.filter(SFeatureBase.id.in_(model_q))

            else:
                q = q.filter(SFeatureBase.feature_en.ilike("%{}%".format(name)))

        paginator = Paginator(q, page_size)
        _page = paginator.page(page)
        total_pages = _page.paginator.total_pages
        data = [serialize(o.to_obj()) for o in _page.object_list]
        if showSearch and len(data) > 0:

            model_q_search = model_q_name
            _model_q_search = ["".join(o) for o in model_q_search]
            # print(_model_q_search,"model_q_search")
            _model_data = [
                f"{d}-v{model_version}" if model_version else f"{d}"
                for d in _model_q_search
            ]
            searchResultModel = ", ".join(_model_data)

    result = {
        "data": data,
        "page": page,
        "total": total_pages,
        "searchResultModel": searchResultModel,
        "showSearch": showSearch,
    }
    return rsp.success(result)


"""
@app.route("/api/features", methods=["GET"])
@cross_origin()
@auth.login_required
def registered_features():
    page = request.args.get("page", 1, type=int)
    name = request.args.get("name", "")
    feature_or_model = request.args.get("feature_or_model", "feature")
    page_size = 10

    new_sql_db = get_featuremeta_db()

    with new_sql_db._session() as s:
        q = s.query(SFeatureBase).filter(SFeatureBase.id > 0)
        if name:
            ns, model_name, model_version = parse_env_id(name)
            print(ns, model_name, model_version)
            if ns is None or ns == "feature":
                q = q.filter(SFeatureBase.feature_en.like("%{}%".format(name)))
            elif ns == "model" and model_name:
                if model_version is None:
                    model_q = s.query(SFeatureModel).filter(
                        SFeatureModel.name.like("%{}%".format(model_name))
                    )
                    feature_ids = [serialize(o.to_obj())["feature_id"] for o in model_q]
                    q = s.query(SFeatureBase).filter(
                        SFeatureBase.id.in_(list(set(feature_ids)))
                    )

                else:
                    model_q = s.query(SFeatureModel).filter(
                        SFeatureModel.name.like("%{}%".format(model_name))
                    )
                    model_q_version = model_q.filter(
                        SFeatureModel.version.like("%{}%".format(model_version))
                    )
                    feature_ids = [
                        serialize(o.to_obj())["feature_id"] for o in model_q_version
                    ]
                    q = s.query(SFeatureBase).filter(
                        SFeatureBase.id.in_(list(set(feature_ids)))
                    )
            else:
                q = q.filter(SFeatureBase.feature_en.like("%{}%".format(name)))

        paginator = Paginator(q, page_size)
        _page = paginator.page(page)
        total_pages = _page.paginator.total_pages
        data = [serialize(o.to_obj()) for o in _page.object_list]

    result = {"data": data, "page": page, "total": total_pages}
    return rsp.success(result)
"""


@app.route("/api/features/add_feature", methods=["POST"])
@cross_origin()
@auth.login_required
def add_feature():
    try:
        feature_cn = request.get_json()["name"]
        feature_en = request.get_json()["feature_en"]
        description = request.get_json()["description"]
        feature_type = request.get_json()["type"]
        user_name = request.get_json()["user"]
        feature_cat = request.get_json()["feature_cat"]
        gen_freq = request.get_json()["gen_freq"]
        gen_from = request.get_json()["gen_from"]
        status = request.get_json().get("status", "production")
        new_sql_db = get_featuremeta_db()

        obj = SFeatureBase(
            feature_cn=str(feature_cn),
            author=user_name,
            feature_en=feature_en,
            description=description,
            feature_type=feature_type,
            feature_cat=feature_cat,
            gen_freq=gen_freq,
            gen_from=gen_from,
            status=status,
            updated_at=datetime.datetime.utcnow(),
            created_at=datetime.datetime.utcnow(),
        )
        new_sql_db._create_object(obj)

        return rsp.success(f"feature {feature_en} added success!")
    except:
        exc_traceback = str(traceback.format_exc())
        return rsp.failed(exc_traceback)


@app.route("/api/features/add_feature_model", methods=["POST"])
@cross_origin()
@auth.login_required
def add_feature_model():
    try:
        feature_id = request.get_json()["feature_id"]
        model_name = request.get_json()["name"]
        model_version = request.get_json()["version"]
        description = request.get_json()["description"]
        user_name = request.get_json()["user_name"]

        status = request.get_json().get("status", "production")
        new_sql_db = get_featuremeta_db()
        with new_sql_db._session() as s:
            query = s.query(SFeatureModel)
            _obj = query.filter_by(
                name=model_name, version=str(model_version), feature_id=int(feature_id)
            ).first()
        if _obj:
            return rsp.failed("Duplicate value for 'name' and 'version'")
        obj = SFeatureModel(
            name=str(model_name),
            version=model_version,
            author=user_name,
            description=description,
            status=status,
            feature_id=int(feature_id),
            updated_at=datetime.datetime.utcnow(),
            created_at=datetime.datetime.utcnow(),
        )
        new_sql_db._create_object(obj)

        return rsp.success(f"feature {model_name} added success!")
    except:
        exc_traceback = str(traceback.format_exc())
        return rsp.failed(exc_traceback)


@app.route("/api/features/get_feature_models", methods=["GET"])
@cross_origin()
@auth.login_required
def get_feature_models():
    page = request.args.get("page", 1, type=int)
    name = request.args.get("name", "")
    feature_id = request.args.get("feature_id", 1)

    page_size = 10

    new_sql_db = get_featuremeta_db()

    with new_sql_db._session() as s:
        q = s.query(SFeatureModel).filter(SFeatureModel.feature_id == int(feature_id))
        if name:
            q = q.filter(SFeatureModel.name.like("%{}%".format(name)))
        paginator = Paginator(q, page_size)
        _page = paginator.page(page)
        total_pages = _page.paginator.total_pages
        data = [serialize(o.to_obj()) for o in _page.object_list]

    result = {"data": data, "page": page, "total": total_pages}
    return rsp.success(result)


@app.route("/api/features/edit_feature_model", methods=["POST"])
@cross_origin()
@auth.login_required
def edit_feature_model():
    model_name = request.get_json()["name"]
    model_version = request.get_json()["version"]
    description = request.get_json()["description"]
    user_name = request.get_json()["user_name"]
    status = request.get_json().get("status", "production")
    new_sql_db = get_featuremeta_db()
    updated_at = datetime.datetime.utcnow()
    if user_name != "leepand":
        return rsp.nopriv("无操作权限")
    with new_sql_db._session() as s:
        p = (
            s.query(SFeatureModel)
            .filter(SFeatureModel.name == model_name)
            .update(
                {
                    "version": str(model_version),
                    "description": description,
                    "updated_at": updated_at,
                    "status": status,
                }
            )
        )

    return rsp.success("edit feature's model info success")


@app.route("/api/features/del_feature_model", methods=["POST"])
@cross_origin()
@auth.login_required
def del_feature_model():
    model_id = request.get_json()["model_id"]
    user_name = request.get_json()["user_name"]
    new_sql_db = get_featuremeta_db()
    if user_name != "leepand":
        return rsp.nopriv("无操作权限")
    ids = [model_id]
    try:
        for _id in ids:
            with new_sql_db._session() as s:
                q = s.query(SFeatureModel).filter(SFeatureModel.id == _id)
                q_list = [o.to_obj() for o in q.all()]
                # print(q_list,"q_list")
                if len(q_list) > 0:
                    author = "leepand"
                    # print(user_name,"sd",author,type(user_name),type(author))
                    if author != user_name:
                        return rsp.nopriv("无操作权限")
                    else:
                        q.delete(synchronize_session=False)

        return rsp.success("删除成功")
    except:
        return rsp.delprojfailed("删除有误")


@app.route("/api/features/del_features", methods=["POST"])
@cross_origin()
@auth.login_required
def del_features():
    ids = request.get_json()["ids"]
    user_name = request.get_json()["user_name"]
    new_sql_db = get_featuremeta_db()
    try:
        for _id in ids:
            with new_sql_db._session() as s:
                q = s.query(SFeatureBase).filter(SFeatureBase.id == _id)
                q_list = [o.to_obj() for o in q.all()]
                # print(q_list,"q_list")
                if len(q_list) > 0:
                    author = "leepand"
                    # print(user_name,"sd",author,type(user_name),type(author))
                    if author != user_name:
                        return rsp.nopriv("无操作权限")
                    else:
                        q.delete(synchronize_session=False)

        return rsp.success("删除成功")
    except:
        return rsp.delprojfailed("删除有误")


# 编辑特征信息
@app.route("/api/features/edit_feature", methods=["POST"])
@cross_origin()
@auth.login_required
def edit_feature():
    feature_cn = request.get_json()["feature_cn"]
    feature_id = request.get_json()["feature_id"]
    feature_type = request.get_json()["type"]
    feature_cat = request.get_json()["feature_cat"]
    gen_from = request.get_json()["gen_from"]
    description = request.get_json()["description"]
    user_name = request.get_json()["user_name"]
    status = request.get_json().get("status", "production")
    new_sql_db = get_featuremeta_db()
    updated_at = datetime.datetime.utcnow()
    if user_name != "leepand":
        return rsp.nopriv("无操作权限")
    with new_sql_db._session() as s:
        p = (
            s.query(SFeatureBase)
            .filter(SFeatureBase.id == feature_id)
            .update(
                {
                    "gen_from": gen_from,
                    "description": description,
                    "feature_cn": feature_cn,
                    "feature_type": feature_type,
                    "feature_cat": feature_cat,
                    "updated_at": updated_at,
                    "status": status,
                }
            )
        )

    return rsp.success("edit feature info success")


# 修改特征描述
@app.route("/api/features/edit_feature_desc", methods=["POST"])
@cross_origin()
@auth.login_required
def edit_feature_desc():
    feature_id = request.get_json()["feature_id"]
    description = request.get_json()["description"]
    user_name = request.get_json()["user_name"]
    new_sql_db = get_featuremeta_db()
    updated_at = datetime.datetime.utcnow()
    if user_name != "leepand":
        return rsp.nopriv("无操作权限")
    with new_sql_db._session() as s:
        p = (
            s.query(SFeatureBase)
            .filter(SFeatureBase.id == int(feature_id))
            .update({"description": description, "updated_at": updated_at})
        )

    return rsp.success("edit feature desc success")


# 获取特征的元数据
@app.route("/api/features/get_feature_metadata", methods=["GET"])
@cross_origin()
@auth.login_required
def get_feature_metadata():
    try:
        feature_id = request.args.get("feature_id")
        new_sql_db = get_featuremeta_db()
        with new_sql_db._session() as s:
            q = s.query(SFeatureBase).filter(SFeatureBase.id == feature_id)
            data = [serialize(o.to_obj()) for o in q.all()]

        results = {"data": data[0]}
        return rsp.success(results)
    except:
        exc_traceback = str(traceback.format_exc())
        # print(exc_traceback,"exc_traceback")
        return rsp.failed(exc_traceback)
