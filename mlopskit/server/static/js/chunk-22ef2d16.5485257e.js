(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["chunk-22ef2d16"],{"287c":function(e,t,a){},4928:function(e,t,a){e.exports=a.p+"img/icon-yes.d2f9f035.svg"},"4ce3":function(e,t,a){"use strict";a.r(t);var s=function(){var e=this,t=e.$createElement,s=e._self._c||t;return s("section",{staticStyle:{"margin-left":"15px","margin-right":"15px","margin-top":"15px"}},[s("el-divider"),s("el-descriptions",{staticClass:"margin-top",attrs:{title:"",column:3,size:e.size}},[s("template",{slot:"title"},[s("span",[e._v(e._s(e.regedModel.name))])]),s("template",{slot:"extra"},["all"===e.firstID?s("router-link",{staticStyle:{"text-decoration":"none",color:"aliceblue"},attrs:{to:{name:"模型运营",params:{model_name:this.$route.params.model_name}}}},[s("el-button",{staticClass:"return-list"},[s("i",{staticClass:"el-icon-arrow-left",staticStyle:{"margin-right":"5px"}}),e._v("返回模型运营中心")])],1):e._e()],1),s("el-descriptions-item",{attrs:{label:"模型名称"}},[e._v(e._s(e.regedModel.name))]),s("el-descriptions-item",{attrs:{label:"创建时间"}},[s("timeago",{attrs:{datetime:e.regedModel.creation_timestamp,locale:"zh-CN"}})],1),s("el-descriptions-item",{attrs:{label:"最近修改时间"}},[s("timeago",{attrs:{datetime:e.regedModel.last_updated_timestamp,locale:"zh-CN"}})],1)],2),s("el-collapse",{staticStyle:{"margin-bottom":"10px"},on:{change:e.handleChange},model:{value:e.activeNames,callback:function(t){e.activeNames=t},expression:"activeNames"}},[s("el-collapse-item",{attrs:{title:"模型描述",name:"1"}},[e.descvisalble?s("span",[e._v(e._s(e.regedModel.description)+"  ")]):e._e(),e.descvisalble?s("el-button",{attrs:{type:"text"},on:{click:e.handleEdit}},[s("i",{staticClass:"el-icon-edit"})]):e._e(),s("el-input",{directives:[{name:"show",rawName:"v-show",value:e.descEditable,expression:"descEditable"}],staticStyle:{width:"60%"},attrs:{type:"textarea",rows:3},model:{value:e.editModelMeta.description,callback:function(t){e.$set(e.editModelMeta,"description",t)},expression:"editModelMeta.description"}}),s("div",[s("el-button",{directives:[{name:"show",rawName:"v-show",value:e.descEditable,expression:"descEditable"}],staticStyle:{"margin-right":"0px"},attrs:{type:"text",icon:"el-icon-arrow-left"},on:{click:e.handelCancel}},[e._v("取消")]),s("el-button",{directives:[{name:"show",rawName:"v-show",value:e.descEditable,expression:"descEditable"}],staticStyle:{align:"right"},attrs:{type:"text",icon:"el-icon-check",circle:""},on:{click:e.submitSave}},[e._v("保存")])],1)],1),s("el-collapse-item",{attrs:{title:"模型版本列表",name:"2"}},[s("el-col",{staticClass:"toolbar",staticStyle:{"padding-bottom":"0px"},attrs:{span:24}},[s("el-radio-group",{staticStyle:{"margin-bottom":"10px"},model:{value:e.isall,callback:function(t){e.isall=t},expression:"isall"}},[s("el-radio-button",{attrs:{label:!0}},[e._v("All")]),s("el-radio-button",{attrs:{label:!1}},[e._v("Active")])],1)],1),s("el-table",{directives:[{name:"loading",rawName:"v-loading",value:e.listLoading,expression:"listLoading"}],staticStyle:{width:"100%"},attrs:{data:e.modelversions,"highlight-current-row":""},on:{"selection-change":e.selsChange}},[s("el-table-column",{attrs:{type:"selection","min-width":"5%"}}),s("el-table-column",{attrs:{prop:"version",label:"版本","min-width":"15%",sortable:"","show-overflow-tooltip":""},scopedSlots:e._u([{key:"default",fn:function(t){return[s("img",{directives:[{name:"show",rawName:"v-show",value:t.row.status,expression:"scope.row.status"}],attrs:{src:a("4928")}}),s("router-link",{staticStyle:{"text-decoration":"none"},attrs:{to:{name:"模型版本详情",params:{version_id:t.row.version,model_name:t.row.name}}}},[e._v("\n              "+e._s("Version  "+t.row.version)+"\n            ")])]}}])}),s("el-table-column",{attrs:{prop:"creation_timestamp",label:"上线时间","min-width":"28%",sortable:"","show-overflow-tooltip":""},scopedSlots:e._u([{key:"default",fn:function(e){return[s("timeago",{attrs:{datetime:e.row.creation_timestamp,locale:"zh-CN"}})]}}])}),s("el-table-column",{attrs:{prop:"tags[0].value",label:"责任人","min-width":"15%",sortable:"","show-overflow-tooltip":""}}),s("el-table-column",{attrs:{prop:"current_stage",label:"所处阶段","min-width":"10%",sortable:""},scopedSlots:e._u([{key:"default",fn:function(t){return["Production"===t.row.current_stage?s("el-tag",{attrs:{type:"success"}},[e._v(e._s(t.row.current_stage))]):"Staging"===t.row.current_stage?s("el-tag",{attrs:{type:"warning"}},[e._v(e._s(t.row.current_stage))]):s("el-tag",{attrs:{type:"info"}},[e._v(e._s(t.row.current_stage))])]}}])}),s("el-table-column",{attrs:{prop:"description",label:"版本描述","min-width":"35%"},scopedSlots:e._u([{key:"default",fn:function(t){return[""===t.row.description?s("span",[e._v("无")]):s("span",[e._v(e._s(t.row.description))])]}}])})],1),s("el-col",{staticClass:"toolbar",attrs:{span:24}},[s("el-pagination",{staticStyle:{float:"right"},attrs:{layout:"prev, pager, next","page-size":20,"page-count":e.total},on:{"current-change":e.handleCurrentChange}})],1)],1)],1),s("br")],1)},o=[],i=a("4ec3"),n=a("c1df"),l=a.n(n),r={data:function(){return{modelversions:[],isall:!0,regedModel:{},descvisalble:!0,descEditable:!1,editModelMeta:{description:""},activeNames:["1","2"],firstID:"all",altListData:[],moment:l.a,listLoading:!1,filters:{name:""},total:0,page:1,sels:[]}},filters:{formatDate:function(e){var t=new Date(e),a=t.getFullYear(),s=t.getMonth()+1;s=s<10?"0"+s:s;var o=t.getDate();o=o<10?"0"+o:o;var i=t.getHours();i=i<10?"0"+i:i;var n=t.getMinutes();n=n<10?"0"+n:n;var l=t.getSeconds();return l=l<10?"0"+l:l,a+"-"+s+"-"+o+" "+i+":"+n+":"+l}},watch:{isall:function(){this.getModelVersionsInfo(this.isall)}},methods:{getModelVersionsInfo:function(e){var t=this;this.stage_btn=e?"all":"active";var a={user_key:JSON.parse(sessionStorage.getItem("name")),stage_btn:this.stage_btn,name:this.$route.params.model_name};console.log(a,"paraar");var s={"Content-Type":"application/json",Authorization:"Token "+JSON.parse(sessionStorage.getItem("token"))};Object(i["A"])(s,a).then((function(e){t.listLoading=!1;var a=e.msg,s=e.code,o=e.data;"999999"===s?(t.modelversions=o.data,console.log(t.modelversions,"self.modelversions")):t.$message.error({message:a,center:!0})}))},getModelsMetaData:function(){var e=this,t={user_key:JSON.parse(sessionStorage.getItem("name")),name:this.$route.params.model_name},a={"Content-Type":"application/json",Authorization:"Token "+JSON.parse(sessionStorage.getItem("token"))};Object(i["w"])(a,t).then((function(t){e.listLoading=!1;var a=t.msg,s=t.code,o=t.data;"999999"===s?(e.regedModel=o,console.log(e.regedModel,"self.regedModel")):e.$message.error({message:a,center:!0})}))},submitSave:function(){var e=this,t=this,a=JSON.stringify({model_name:t.$route.params.model_name,description:t.editModelMeta.description,user_name:JSON.parse(sessionStorage.getItem("name"))});console.log(a,"params");var s={"Content-Type":"application/json",Authorization:"Token "+JSON.parse(sessionStorage.getItem("token"))};Object(i["d"])(s,a).then((function(a){var s=a.msg,o=a.code;"999999"===o?(t.$message({message:"添加成功",center:!0,type:"success"}),e.descEditable=!1,e.descvisalble=!0,e.editModelMeta.description="",t.getModelsMetaData()):"999997"===o?t.$message.error({message:s,center:!0}):(t.$message.error({message:s,center:!0}),e.editModelMeta.description="",e.descEditable=!1,e.descvisalble=!0,t.getModelsMetaData())}))},handelCancel:function(){this.descEditable=!1,this.descvisalble=!0,this.editModelMeta.description=""},handleEdit:function(){this.descEditable=!0,this.descvisalble=!1,this.editModelMeta.description=this.regedModel.description},handleChange:function(e){console.log(e)},handleCurrentChange:function(e){this.page=e}},mounted:function(){this.getModelsMetaData(),this.isall?this.stage_btn="all":this.stage_btn="active",this.getModelVersionsInfo(this.isall)}},c=r,d=(a("d63e"),a("2877")),m=Object(d["a"])(c,s,o,!1,null,"5933a4c9",null);t["default"]=m.exports},d63e:function(e,t,a){"use strict";a("287c")}}]);
//# sourceMappingURL=chunk-22ef2d16.5485257e.js.map