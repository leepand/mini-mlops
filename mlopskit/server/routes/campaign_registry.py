from .. import app, auth, sql_db
from flask import request
from flask_cors import cross_origin
import datetime
import traceback

from ..models.models import SDataCampaign, SAbExpCase, SAbExpOps, SUsers
from sqlalchemy_paginator import Paginator
from pyjackson import deserialize, serialize

from .response import Response
from structlog import get_logger


from abkit.models import Experiment
import abkit.db as db
from ..utils.misc import (
    experiment_list,
    archived,
    paused,
    find_or_404,
    simple_markdown,
    determine_period,
    update_experiment_description,
    delete_experiment,
    set_winner,
    reset_winner,
    toggle_experiment_archive,
    reset_experiment,
    toggle_experiment_pause,
)

logger = get_logger(__name__)

rsp = Response()


@app.route("/api/campaigns", methods=["GET"])
@cross_origin()
@auth.login_required
def registered_campaigns():
    page_size = 10
    page = request.args.get("page", 1, type=int)
    name = request.args.get("name", "")
    user_name = request.args.get("user_key", "")

    with sql_db._session() as s:
        q = s.query(SDataCampaign).filter(SDataCampaign.id > 0)
        if name:
            q = q.filter(SDataCampaign.name.like("%{}%".format(name)))
        paginator = Paginator(q, page_size)
        _page = paginator.page(page)
        total_pages = _page.paginator.total_pages
        data = [serialize(o.to_obj()) for o in _page.object_list]

    result = {"data": data, "page": page, "total": total_pages}
    return rsp.success(result)


@app.route("/api/campaigns/del_campaigns", methods=["POST"])
@cross_origin()
@auth.login_required
def del_campaigns():
    ids = request.get_json()["ids"]
    user_name = request.get_json()["user_name"]
    try:
        for _id in ids:
            with sql_db._session() as s:
                q = s.query(SDataCampaign).filter(SDataCampaign.id == _id)
                q_list = [o.to_obj() for o in q.all()]
                # print(q_list,"q_list")
                if len(q_list) > 0:
                    author = q_list[0].author
                    # print(user_name,"sd",author,type(user_name),type(author))
                    if author != user_name:
                        return rsp.nopriv("无操作权限")
                    else:
                        q.delete(synchronize_session=False)

        return rsp.success("删除成功")
    except:
        return rsp.delprojfailed("删除有误")


@app.route("/api/campaigns/add_campaign", methods=["POST"])
@cross_origin()
@auth.login_required
def add_campaign():
    try:
        campaign_name = request.get_json()["name"]
        description = request.get_json()["description"]
        campaign_type = request.get_json()["type"]
        user_name = request.get_json()["user"]

        obj = SDataCampaign(
            name=str(campaign_name),
            description=description,
            data_campaign_type=campaign_type,
            author=user_name,
            campaign_status=0,
            online_date=datetime.datetime.utcnow(),
            expire_date=datetime.datetime.utcnow(),
            creation_date=datetime.datetime.utcnow(),
        )
        sql_db._create_object(obj)

        return rsp.success("campaign added success!")
    except:
        exc_traceback = str(traceback.format_exc())
        return rsp.failed(exc_traceback)


@app.route("/api/campaigns/abexps", methods=["GET"])
@cross_origin()
@auth.login_required
def registered_abexps():
    page_size = 5
    page = request.args.get("page", 1, type=int)
    name = request.args.get("name", "")
    user_name = request.args.get("user_name", "")
    campaign_id = request.args.get("campaign_id", 1)
    _data = []
    with sql_db._session() as s:
        q = s.query(SAbExpCase)
        q = q.filter(SAbExpCase.data_campaign_id == campaign_id)
        if name:
            q = q.filter(SAbExpCase.name.like("%{}%".format(name)))
        paginator = Paginator(q, page_size)
        _page = paginator.page(page)
        total_pages = _page.paginator.total_pages
        data = [serialize(o.to_obj()) for o in _page.object_list]
        for abgroup in data:
            ops = sql_db._get_objects(SAbExpOps, SAbExpOps.ab_id == abgroup["id"])
            abgroup["abalt_cnt"] = len(ops)
            _data.append(abgroup)

    result = {"data": _data, "page": page, "total": total_pages}
    return rsp.success(result)


@app.route("/api/campaigns/del_abexp", methods=["POST"])
@cross_origin()
@auth.login_required
def del_campaign_exps():
    ab_id = request.get_json()["ab_id"]
    campaign_id = request.get_json()["campaign_id"]
    user_name = request.get_json()["user_name"]
    ids = [ab_id]
    try:
        for _id in ids:
            with sql_db._session() as s:
                q_user = s.query(SUsers).filter(SUsers.name == user_name)
                q_user_list = [o.to_obj() for o in q_user.all()]
                # print(q_user_list[0].name,"q_user_list")
                q = s.query(SAbExpCase).filter(SAbExpCase.id == _id)
                q_list = [o.to_obj() for o in q.all()]
                # print(q_list,"q_list")
                if len(q_list) > 0:
                    author_id = q_list[0].user_id
                    # print(author_id,"author")
                    # print(user_name,"sd",author,type(user_name),type(author))
                    if author_id != q_user_list[0].id:
                        return rsp.nopriv("无操作权限")
                    else:
                        q.delete(synchronize_session=False)

        return rsp.success("删除成功")
    except:
        return rsp.delprojfailed("删除有误")


@app.route("/api/campaigns/get_campaign_metadata", methods=["GET"])
@cross_origin()
@auth.login_required
def get_campaign_metadata():
    try:
        campaign_id = request.args.get("campaign_id", "")

        data = sql_db._get_objects(SDataCampaign, SDataCampaign.id == campaign_id)
        data2 = sql_db._get_objects(
            SAbExpCase, SAbExpCase.data_campaign_id == campaign_id
        )

        meta_campaign = {}
        meta_campaign["campaign"] = [serialize(o) for o in data][0]
        meta_campaign["strategy_cnt"] = len(data2)
        results = {"data": meta_campaign}
        return rsp.success(results)
    except:
        exc_traceback = str(traceback.format_exc())
        # print(exc_traceback,"exc_traceback")
        return rsp.failed(exc_traceback)


# 获取实验的元数据
@app.route("/api/campaigns/get_exp_metadata", methods=["GET"])
@cross_origin()
@auth.login_required
def get_exp_metadata():
    try:
        campaign_id = request.args.get("campaign_id", "")
        ab_id = request.args.get("ab_id", "")
        with sql_db._session() as s:
            q = s.query(SAbExpCase).filter(SAbExpCase.id == ab_id)
            data = [serialize(o.to_obj()) for o in q.all()]

        results = {"data": data[0]}
        return rsp.success(results)
    except:
        exc_traceback = str(traceback.format_exc())
        # print(exc_traceback,"exc_traceback")
        return rsp.failed(exc_traceback)


@app.route("/api/campaigns/case_exp_altlist", methods=["GET"])
@cross_origin()
@auth.login_required
def case_exp_altlist():
    try:
        campaign_id = request.args.get("campaign_id", "")
        ab_id = request.args.get("ab_id", "")
        with sql_db._session() as s:
            q = s.query(SAbExpOps).filter(SAbExpOps.ab_id == ab_id)
            data = [serialize(o.to_obj()) for o in q.all()]

        results = {"data": data}
        return rsp.success(results)
    except:
        exc_traceback = str(traceback.format_exc())
        # print(exc_traceback,"exc_traceback")
        return rsp.failed(exc_traceback)


# 修改活动描述
@app.route("/api/campaigns/edit_campaign_desc", methods=["POST"])
@cross_origin()
@auth.login_required
def edit_campaign_desc():
    campaign_id = request.get_json()["campaign_id"]
    description = request.get_json()["description"]
    user_name = request.get_json()["user_name"]
    with sql_db._session() as s:
        p = (
            s.query(SDataCampaign)
            .filter(SDataCampaign.id == campaign_id)
            .update({"description": description})
        )

    return rsp.success("edit campaign desc success")


@app.route("/api/campaigns/add_ab_exp", methods=["POST"])
@cross_origin()
@auth.login_required
def add_ab_exp():
    try:
        ab_name = request.get_json()["name"]
        campaign_id = request.get_json()["campaign_id"]
        description = request.get_json()["description"]
        user_name = request.get_json()["user_name"]
        logger.debug("Getting %ss", ab_name=ab_name)
        obj = SAbExpCase(
            name=str(ab_name),
            description=description,
            data_campaign_id=campaign_id,
            user_id=1,
            app_type="基于数据策略",
            creation_date=datetime.datetime.utcnow(),
        )
        sql_db._create_object(obj)
        return rsp.success("abexp added success!")
    except:
        exc_traceback = str(traceback.format_exc())
        return rsp.failed(exc_traceback)


# 获取实验组元数据
@app.route("/api/campaigns/get_abexp_metadata", methods=["GET"])
@cross_origin()
@auth.login_required
def get_abexp_metadata():
    ab_id = request.args.get("ab_id", 1)
    kpi = request.args.get("abkpi", None)
    if kpi == "default":
        kpi = None

    period = determine_period()
    p = sql_db._get_objects(SAbExpCase, SAbExpCase.id == ab_id)
    ab_info = [serialize(o) for o in p]
    data = {}
    abname = ab_info[0]["name"]
    camp = sql_db._get_objects(
        SDataCampaign, SDataCampaign.id == ab_info[0]["data_campaign_id"]
    )
    create_date = ab_info[0]["creation_date"]
    data = ab_info[0]
    camp_name = [serialize(o) for o in camp][0]["name"]
    data["abname"] = abname
    data["camp_name"] = camp_name
    data["create_date"] = create_date

    bRet, experiment = find_or_404(abname, kpi=kpi)
    if bRet:
        period = "day"
        obj = simple_markdown(experiment.objectify_by_period(period))
        # exp_out=obj['alternatives']#实验各组详情数据
        if not obj["description"]:
            ab_dynamic_description = "目前还没有实验动态描述，赶紧添加吧"
        else:
            ab_dynamic_description = obj["description"]
    else:
        ab_dynamic_description = "实验尚未开始"
    data["ab_dynamic_description"] = ab_dynamic_description
    result = {"data": data}

    return rsp.success(result)


@app.route("/api/campaigns/add_exp_alt", methods=["POST"])
@cross_origin()
@auth.login_required
def add_exp_alt():
    try:
        ab_id = request.get_json()["ab_id"]
        # abname = request.get_json()["abname"]
        # description = request.get_json()["description"]
        altList = request.get_json()["expRegData"]
        # description = request.get_json()['description']
        if len(altList) < 1:
            return rsp.failed("请输入实验组信息")
        for alt_dict in altList:
            altName = alt_dict["expName"]
            modelname = alt_dict["name"]
            exposureNum = alt_dict["exposureNum"]

            obj = SAbExpOps(
                name=str("abname"),
                alt_name=altName,
                description="description",
                exposure_ratio=str(exposureNum),
                model_name=modelname,
                model_id=1,
                ab_id=ab_id,
                creation_date=datetime.datetime.utcnow(),
            )
            sql_db._create_object(obj)
        return rsp.success("altlist added success!")
    except:
        exc_traceback = str(traceback.format_exc())
        return rsp.failed(exc_traceback)


@app.route("/api/campaigns/ab_exp_altlist", methods=["GET"])
@cross_origin()
@auth.login_required
def registered_altlist():
    campaign_id = request.args.get("campaign_id", 1, type=int)
    ab_id = request.args.get("ab_id", 1)
    object_list = sql_db._get_objects(SAbExpOps, SAbExpOps.ab_id == ab_id)
    data = [serialize(o) for o in object_list]

    result = {"data": data}
    return rsp.success(result)


"""
A/B testing 详情及ops系列
"""
# 查看ab case results
@app.route("/api/abtesting/report/alt_table_report", methods=["GET"])
@cross_origin()
@auth.login_required
def alt_table_report():
    page_size = 10
    ab_id = request.args.get("ab_id", 1)
    time = request.args.get("time")
    abkpi = request.args.get("abkpi")

    p = sql_db._get_objects(SAbExpCase, SAbExpCase.id == ab_id)
    ab_info = [serialize(o) for o in p]

    abname = ab_info[0]["name"]
    if abkpi and abkpi != "default":
        kpi = abkpi
    else:
        kpi = None
    period = determine_period()

    bRet, experiment = find_or_404(abname, kpi=kpi)
    if bRet:
        if not time:
            period = "day"
        else:
            period = time  # determine_period()
        obj = simple_markdown(experiment.objectify_by_period(period))
        # exp_out=obj['alternatives']#实验各组详情数据
        if not obj["description"]:
            description = "目前还没有实验描述，赶紧添加吧"
        else:
            description = obj["description"]
        if len(obj["kpis"]) > 0:
            kpis = obj["kpis"]
        else:
            kpis = "defalut"

        obj["kpis"].append("default")
        data = obj
    else:
        data = {}

    return rsp.success(data)


# 设置胜利组
@app.route("/api/abtesting/report/abset_winner", methods=["POST"])
@cross_origin()
@auth.login_required
def abset_winner():
    ab_id = request.get_json()["ab_id"]
    altname = request.get_json()["altname"]

    p = sql_db._get_objects(SAbExpCase, SAbExpCase.id == ab_id)
    ab_info = [serialize(o) for o in p]

    abname = ab_info[0]["name"]

    set_winner(abname, altname)
    return rsp.success("setwinner success")


# 重置胜利组
@app.route("/api/abtesting/report/resetWinner", methods=["POST"])
@cross_origin()
@auth.login_required
def resetWinner():
    ab_id = request.get_json()["ab_id"]

    p = sql_db._get_objects(SAbExpCase, SAbExpCase.id == ab_id)
    ab_info = [serialize(o) for o in p]

    abname = ab_info[0]["name"]

    reset_winner(abname)
    return rsp.success("resetwinner success")


# 修改实验描述
@app.route("/api/abtesting/report/edit_ab_desc", methods=["POST"])
@cross_origin()
@auth.login_required
def edit_ab_desc():
    ab_id = request.get_json()["ab_id"]
    description = request.get_json()["description"]
    abkpi = request.get_json()["abkpi"]
    # with sql_db._session() as s:
    #    p=s.query(SAbExpCase).filter(SAbExpCase.id==ab_id).update({"description":description})
    _p = sql_db._get_objects(SAbExpCase, SAbExpCase.id == ab_id)
    ab_info = [serialize(o) for o in _p]

    abname = ab_info[0]["name"]
    if not description:
        description = "machine learning a/b desc"
    if abkpi:
        if abkpi == "default":
            abkpi = None
        _, experiment = find_or_404(abname, kpi=abkpi)
        experiment.update_description(description)
    else:
        update_experiment_description(abname, description)
    return rsp.success("edit desc success")


# 停止实验
@app.route("/api/abtesting/report/stop_exp", methods=["POST"])
@cross_origin()
@auth.login_required
def stop_exp():
    ab_id = request.get_json()["ab_id"]

    _p = sql_db._get_objects(SAbExpCase, SAbExpCase.id == ab_id)
    ab_info = [serialize(o) for o in _p]

    abname = ab_info[0]["name"]
    toggle_experiment_archive(abname)
    return rsp.success("exp ops success")


# 重置实验
@app.route("/api/abtesting/report/reset_exp", methods=["POST"])
@cross_origin()
@auth.login_required
def reset_exp():
    ab_id = request.get_json()["ab_id"]

    _p = sql_db._get_objects(SAbExpCase, SAbExpCase.id == ab_id)
    ab_info = [serialize(o) for o in _p]

    abname = ab_info[0]["name"]
    reset_experiment(abname)
    return rsp.success("resetExp success")


# 暂停/开启实验
@app.route("/api/abtesting/report/pause_exp", methods=["POST"])
@cross_origin()
@auth.login_required
def pause_exp():
    ab_id = request.get_json()["ab_id"]
    _p = sql_db._get_objects(SAbExpCase, SAbExpCase.id == ab_id)
    ab_info = [serialize(o) for o in _p]

    abname = ab_info[0]["name"]

    toggle_experiment_pause(abname)
    return rsp.success("exp ops success")


@app.route("/api/models/api_list", methods=["GET"])
@cross_origin()
@auth.login_required
def get_model_services():
    try:
        results = {}
        return rsp.success(results)
    except:
        exc_traceback = str(traceback.format_exc())
        # print(exc_traceback,"exc_traceback")
        return rsp.failed(exc_traceback)
