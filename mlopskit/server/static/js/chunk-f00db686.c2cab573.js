(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["chunk-f00db686"],{"2ba3":function(a,t,s){"use strict";s.r(t);var n=function(){var a=this,t=a.$createElement,s=a._self._c||t;return s("div",{staticClass:"main-a"},[s("el-row",{attrs:{span:24}},[s("el-col",{staticClass:"inline",attrs:{span:6}},[s("el-card",{staticClass:"box-card"},[s("h1",[a._v(a._s(a.campaign_cnt))]),s("div",[a._v("营销活动总数")])])],1),s("el-col",{staticClass:"inline",attrs:{span:6}},[s("el-card",{staticClass:"box-card"},[s("h1",[a._v(a._s(a.ab_exp_cnt))]),s("div",[a._v("A/B在线实验总数")])])],1),s("el-col",{staticClass:"inline",attrs:{span:6}},[s("el-card",{staticClass:"box-card"},[s("h1",[s("router-link",{staticStyle:{cursor:"pointer",color:"#0000ff","text-decoration":"none"},attrs:{to:{name:"模型中心",params:{}}}},[a._v("\n            "+a._s(a.models_cnt)+"\n          ")])],1),s("div",[a._v("注册的模型总数")])])],1)],1),s("el-row",{attrs:{span:24}},[s("el-col",{staticClass:"inline",attrs:{span:6}},[s("el-card",{staticClass:"box-card"},[s("h1",[s("el-link",{attrs:{type:"primary"}},[a._v(a._s(a.pay_cvr_lift)+"%")])],1),s("div",[a._v("付费转化率提升")])])],1),s("el-col",{staticClass:"inline",attrs:{span:6}},[s("el-card",{staticClass:"box-card"},[s("h1",[a._v(a._s(a.repurchase_lift)+"%")]),s("div",[a._v("复购率提升")])])],1),s("el-col",{staticClass:"inline",attrs:{span:6}},[s("el-card",{staticClass:"box-card"},[s("h1",[a._v(a._s(a.pay_m_lift)+"%")]),s("div",[a._v("付费额提升")])])],1)],1),s("el-row",{attrs:{span:24}},[s("el-col",{staticClass:"inline",attrs:{span:6}},[s("el-card",{staticClass:"box-card"},[s("h1",[a._v(a._s(a.retention_lift)+"%")]),s("div",[a._v("留存提升")])])],1),s("el-col",{staticClass:"inline",attrs:{span:6}},[s("el-card",{staticClass:"box-card"},[s("h1",[a._v(a._s(a.spin_consume_lift)+"%")]),s("div",[a._v("消耗提升")])])],1)],1),s("el-row",{attrs:{span:24}},[s("el-col",{staticClass:"inline",attrs:{span:6}},[s("el-card",{staticClass:"box-card"},[s("h1",[a._v("xx")]),s("div",[a._v("模型调用总次数")])])],1)],1)],1)},e=[],i=s("4ec3"),c={data:function(){return{retention_lift:"x",pay_m_lift:"x",repurchase_lift:"x",pay_cvr_lift:"x",spin_consume_lift:"x",models_cnt:0,ab_exp_cnt:0,campaign_cnt:0,activeNames:["1"]}},methods:{getDashboardInfo:function(){var a=this,t={user_key:JSON.parse(sessionStorage.getItem("name"))},s={"Content-Type":"application/json",Authorization:"Token "+JSON.parse(sessionStorage.getItem("token"))};Object(i["s"])(s,t).then((function(t){var s=t.msg,n=t.code,e=t.data;a.listLoading=!1,"999999"===n?(a.campaign_cnt=e.data.campaign_cnt,a.ab_exp_cnt=e.data.ab_exp_cnt,a.models_cnt=e.data.models_cnt):a.$message.error({message:s,center:!0})}))}},mounted:function(){this.getDashboardInfo()}},l=c,r=(s("3f7a"),s("2877")),o=Object(r["a"])(l,n,e,!1,null,"2fd1ba45",null);t["default"]=o.exports},"3f7a":function(a,t,s){"use strict";s("af4b")},af4b:function(a,t,s){}}]);
//# sourceMappingURL=chunk-f00db686.c2cab573.js.map