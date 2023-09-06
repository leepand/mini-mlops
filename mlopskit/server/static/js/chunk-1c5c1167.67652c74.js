(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["chunk-1c5c1167"],{"32bc":function(e,t,a){"use strict";a.r(t);var s=function(){var e=this,t=e.$createElement,a=e._self._c||t;return a("section",{staticStyle:{"margin-left":"15px","margin-right":"15px","margin-top":"15px"}},[a("el-divider"),a("el-descriptions",{staticClass:"margin-top",attrs:{title:"",column:3,size:e.size}},[a("template",{slot:"title"},[a("span",[e._v(e._s(e.featureMeta.feature_cn))])]),a("template",{slot:"extra"},[a("router-link",{staticStyle:{"text-decoration":"none",color:"aliceblue"},attrs:{to:{name:"特征存储",params:{feature_id:this.$route.params.feature_id}}}},[a("el-button",{staticClass:"return-list"},[a("i",{staticClass:"el-icon-arrow-left",staticStyle:{"margin-right":"5px"}}),e._v("返回特征列表")])],1)],1),a("el-descriptions-item",{attrs:{label:"特征ID"}},[e._v(e._s(e.featureMeta.feature_en))]),a("el-descriptions-item",{attrs:{label:"创建时间"}},[a("timeago",{attrs:{datetime:e.featureMeta.created_at,locale:"zh-CN"}})],1),a("el-descriptions-item",{attrs:{label:"最近更新"}},[a("timeago",{attrs:{datetime:e.featureMeta.updated_at,locale:"zh-CN"}})],1),"production"===e.featureMeta.status?a("el-descriptions-item",{attrs:{label:"特征状态"}},[a("el-tag",{attrs:{size:"small"}},[e._v("生产")])],1):"dev"===e.featureMeta.status?a("el-descriptions-item",{attrs:{label:"特征状态"}},[a("el-tag",{attrs:{size:"small",type:"warning"}},[e._v("开发")])],1):a("el-descriptions-item",{attrs:{label:"特征状态"}},[a("el-tag",{attrs:{size:"small",type:"info"}},[e._v("已下线")])],1)],2),a("el-collapse",{on:{change:e.handleChange},model:{value:e.activeNames,callback:function(t){e.activeNames=t},expression:"activeNames"}},[a("el-collapse-item",{attrs:{title:"特征描述",name:"1"}},[a("span",{directives:[{name:"show",rawName:"v-show",value:e.descvisalble,expression:"descvisalble"}]},[e._v(e._s(e.featureMeta.description)+"  ")]),a("el-button",{directives:[{name:"show",rawName:"v-show",value:e.descvisalble,expression:"descvisalble"}],attrs:{type:"text"},on:{click:e.handleEdit}},[a("i",{staticClass:"el-icon-edit"})]),a("el-input",{directives:[{name:"show",rawName:"v-show",value:e.descEditable,expression:"descEditable"}],staticStyle:{width:"60%"},attrs:{type:"textarea",rows:3},model:{value:e.editFeatureMeta.description,callback:function(t){e.$set(e.editFeatureMeta,"description",t)},expression:"editFeatureMeta.description"}}),a("div",[a("el-button",{directives:[{name:"show",rawName:"v-show",value:e.descEditable,expression:"descEditable"}],staticStyle:{"margin-right":"0px"},attrs:{type:"text",icon:"el-icon-arrow-left"},on:{click:e.handelCancel}},[e._v("取消")]),a("el-button",{directives:[{name:"show",rawName:"v-show",value:e.descEditable,expression:"descEditable"}],staticStyle:{align:"right"},attrs:{type:"text",icon:"el-icon-check",circle:""},on:{click:e.submitSave}},[e._v("保存")])],1)],1),a("el-collapse-item",{attrs:{title:"使用该特征的模型",name:"2"}},[a("el-col",{staticClass:"toolbar",staticStyle:{"padding-bottom":"0px"},attrs:{span:24}},[a("el-form",{attrs:{inline:!0,model:e.filters},nativeOn:{submit:function(e){e.preventDefault()}}},[a("el-form-item",[a("el-input",{attrs:{placeholder:"名称"},nativeOn:{keyup:function(t){return!t.type.indexOf("key")&&e._k(t.keyCode,"enter",13,t.key,"Enter")?null:e.getFeatureModelList(t)}},model:{value:e.filters.name,callback:function(t){e.$set(e.filters,"name",t)},expression:"filters.name"}})],1),a("el-form-item",[a("el-button",{attrs:{type:"primary"},on:{click:e.getFeatureModelList}},[e._v("查询")])],1),a("el-form-item",[a("el-button",{attrs:{type:"primary",icon:"el-icon-plus"},on:{click:e.handleAdd}},[e._v("已注册的模型")])],1)],1)],1),a("el-table",{directives:[{name:"loading",rawName:"v-loading",value:e.listLoading,expression:"listLoading"}],staticStyle:{width:"100%"},attrs:{data:e.ModelList,"highlight-current-row":""},on:{"expand-change":e.expandModelClick}},[a("el-table-column",{attrs:{type:"index",width:"55"}}),a("el-table-column",{attrs:{prop:"name",label:"模型名称","min-width":"20%",sortable:"","show-overflow-tooltip":""},scopedSlots:e._u([{key:"default",fn:function(t){return[a("el-icon",{attrs:{name:"name"}}),a("router-link",{staticStyle:{cursor:"pointer",color:"#0000FF","text-decoration":"underline"},attrs:{to:{name:"模型版本管理",params:{model_name:t.row.name}}}},[e._v(e._s(t.row.name)+"\n                  ")])]}}])}),a("el-table-column",{attrs:{prop:"version",label:"模型版本","min-width":"15%",sortable:"","show-overflow-tooltip":""}}),a("el-table-column",{attrs:{prop:"status",label:"模型状态","min-width":"15%",sortable:"","show-overflow-tooltip":""},scopedSlots:e._u([{key:"default",fn:function(t){return["production"===t.row.status?a("span",{attrs:{label:"特征状态"}},[a("el-tag",{attrs:{size:"small"}},[e._v("生产")])],1):"dev"===t.row.status?a("span",{attrs:{label:"特征状态"}},[a("el-tag",{attrs:{size:"small",type:"warning"}},[e._v("开发")])],1):a("span",{attrs:{label:"特征状态"}},[a("el-tag",{attrs:{size:"small",type:"info"}},[e._v("已下线")])],1)]}}])}),a("el-table-column",{attrs:{prop:"created_at",label:"创建时间","min-width":"15%",sortable:"","show-overflow-tooltip":""},scopedSlots:e._u([{key:"default",fn:function(e){return[a("span",{staticStyle:{"font-size":"16px"}},[a("timeago",{attrs:{datetime:e.row.created_at,locale:"zh-CN"}})],1)]}}])}),a("el-table-column",{attrs:{prop:"description",label:"特征使用详情","min-width":"20%",sortable:""},scopedSlots:e._u([{key:"default",fn:function(t){return[a("span",{staticStyle:{"font-size":"16px"}},[e._v(e._s(t.row.description))])]}}])}),a("el-table-column",{attrs:{label:"操作","min-width":"15%",align:"right"},scopedSlots:e._u([{key:"default",fn:function(t){return[a("el-button",{staticStyle:{"text-align":"right"},attrs:{type:"primary",size:"small"},on:{click:function(a){return e.handleSubModelEdit(t.$index,t.row)}}},[e._v("编辑")]),a("el-button",{staticStyle:{"text-align":"right"},attrs:{type:"danger",size:"small"},on:{click:function(a){return e.handleDel(t.$index,t.row)}}},[e._v("删除")])]}}])})],1),a("el-col",{staticClass:"toolbar",attrs:{span:24}},[a("el-pagination",{staticStyle:{float:"right"},attrs:{layout:"prev, pager, next","page-size":20,"page-count":e.total},on:{"current-change":e.handleCurrentChange}})],1)],1)],1),a("el-dialog",{staticStyle:{width:"85%",left:"12.5%"},attrs:{title:"编辑模型信息",visible:e.editFormVisible,"close-on-click-modal":!1},on:{"update:visible":function(t){e.editFormVisible=t}}},[a("el-form",{ref:"editForm",attrs:{model:e.editForm,"label-width":"80px",rules:e.editFormRules}},[a("el-form-item",{attrs:{label:"模型名称",prop:"name"}},[a("el-input",{attrs:{"auto-complete":"off",disabled:""},model:{value:e.editForm.name,callback:function(t){e.$set(e.editForm,"name","string"===typeof t?t.trim():t)},expression:"editForm.name"}})],1),a("el-row",{attrs:{gutter:24}},[a("el-col",{attrs:{span:12}},[a("el-form-item",{attrs:{label:"模型版本",prop:"version"}},[a("el-input",{attrs:{"auto-complete":"off",disabled:""},model:{value:e.editForm.version,callback:function(t){e.$set(e.editForm,"version","string"===typeof t?t.trim():t)},expression:"editForm.version"}})],1)],1),a("el-col",{attrs:{span:12}},[a("el-form-item",{attrs:{label:"使用状态",prop:"status"}},[a("el-select",{attrs:{placeholder:"请选择"},model:{value:e.editForm.status,callback:function(t){e.$set(e.editForm,"status",t)},expression:"editForm.status"}},e._l(e.StatusOptions,(function(e){return a("el-option",{key:e.value,attrs:{label:e.label,value:e.value}})})),1)],1)],1)],1),a("el-form-item",{attrs:{label:"使用详情",prop:"description"}},[a("el-input",{attrs:{type:"textarea",rows:3},model:{value:e.editForm.description,callback:function(t){e.$set(e.editForm,"description",t)},expression:"editForm.description"}})],1)],1),a("div",{staticClass:"dialog-footer",attrs:{slot:"footer"},slot:"footer"},[a("el-button",{nativeOn:{click:function(t){e.editFormVisible=!1}}},[e._v("取消")]),a("el-button",{attrs:{type:"primary",loading:e.editLoading},nativeOn:{click:function(t){return e.editSubmit(t)}}},[e._v("提交")])],1)],1),a("el-dialog",{staticStyle:{width:"75%",left:"12.5%"},attrs:{title:"新增模型信息",visible:e.addFormVisible,"close-on-click-modal":!1},on:{"update:visible":function(t){e.addFormVisible=t}}},[a("el-form",{ref:"addForm",attrs:{model:e.addForm,"label-width":"80px",rules:e.addFormRules}},[a("el-row",{attrs:{gutter:24}},[a("el-col",{attrs:{span:24}},[a("el-form-item",{attrs:{label:"模型名称",prop:"name"}},[a("el-autocomplete",{staticClass:"inline-input",staticStyle:{width:"100%"},attrs:{"fetch-suggestions":e.querySearchAsync},on:{select:e.handleSelect},model:{value:e.addForm.name,callback:function(t){e.$set(e.addForm,"name","string"===typeof t?t.trim():t)},expression:"addForm.name"}})],1)],1)],1),a("el-form-item",{attrs:{label:"模型版本",prop:"version"}},[a("el-input",{attrs:{"auto-complete":"off"},model:{value:e.addForm.version,callback:function(t){e.$set(e.addForm,"version","string"===typeof t?t.trim():t)},expression:"addForm.version"}})],1),a("el-form-item",{attrs:{label:"使用详情",prop:"description"}},[a("el-input",{attrs:{type:"textarea",rows:3},model:{value:e.addForm.description,callback:function(t){e.$set(e.addForm,"description",t)},expression:"addForm.description"}})],1)],1),a("div",{staticClass:"dialog-footer",attrs:{slot:"footer"},slot:"footer"},[a("el-button",{nativeOn:{click:function(t){e.addFormVisible=!1}}},[e._v("取消")]),a("el-button",{attrs:{type:"primary",loading:e.addLoading},nativeOn:{click:function(t){return e.addSubmit(t)}}},[e._v("提交")])],1)],1)],1)},i=[],o=(a("7f7f"),a("4ec3")),r=a("1157"),n=a.n(r),l=a("c1df"),d=a.n(l),c={data:function(){return{state:"",models:[],timeout:null,StatusOptions:[{label:"生产",value:"production"},{label:"开发",value:"dev"},{label:"已下线",value:"archive"}],editForm:{name:"",version:"",status:"",description:""},editFormVisible:!1,descvisalble:!0,descEditable:!1,featureMeta:{},editFeatureMeta:{description:""},addFormVisible:!1,addLoading:!1,addFormRules:{name:[{required:!0,message:"请输入名称",trigger:"select"},{min:1,max:50,message:"长度在 1 到 50 个字符",trigger:"input"}],version:[{required:!0,message:"请输入版本",trigger:"blur"},{min:1,max:50,message:"长度在 1 到 50 个字符",trigger:"blur"}],description:[{required:!1,message:"请输入版本号",trigger:"blur"},{max:1024,message:"不能超过1024个字符",trigger:"blur"}]},addForm:{name:"",version:"",description:""},activeNames:["1","2"],firstID:"all",altListData:[],moment:d.a,project:"",case:"",ModelList:[],listLoading:!1,filters:{name:""},total:0,page:1,sels:[],activeIndex:""}},methods:{getModelsList:function(){this.listLoading=!0;var e=this,t={page:e.page,user_key:JSON.parse(sessionStorage.getItem("name")),name:e.filters.name},a={"Content-Type":"application/json",Authorization:"Token "+JSON.parse(sessionStorage.getItem("token"))};Object(o["D"])(a,t).then((function(t){e.listLoading=!1;var a=t.msg,s=t.code,i=t.data;"999999"===s?(e.total=i.total,e.models=i.data,e.model_meta=i.model_meta,console.log(e.models,"self.models"),console.log(e.total,"self.total"),console.log(e.model_meta,"self.model_meta")):e.$message.error({message:a,center:!0})}))},querySearchAsync:function(e,t){var a=this.models.map((function(e){return{value:e.name,label:e.name}})),s=e?a.filter(this.createStateFilter(e)):a;clearTimeout(this.timeout),this.timeout=setTimeout((function(){t(s)}),300)},createStateFilter:function(e){return function(t){return 0===t.value.toLowerCase().indexOf(e.toLowerCase())}},handleSelect:function(e){console.log(e)},submitSave:function(){var e=this,t=this,a=JSON.stringify({feature_id:t.$route.params.feature_id,description:t.editFeatureMeta.description,user_name:JSON.parse(sessionStorage.getItem("name"))});console.log(a,"params");var s={"Content-Type":"application/json",Authorization:"Token "+JSON.parse(sessionStorage.getItem("token"))};Object(o["c"])(s,a).then((function(a){var s=a.msg,i=a.code;t.addLoading=!1,"999999"===i?(t.$message({message:"修改成功",center:!0,type:"success"}),e.descEditable=!1,e.descvisalble=!0,e.editFeatureMeta.description="",t.getFeatureMata()):"999997"===i?t.$message.error({message:s,center:!0}):(t.$message.error({message:s,center:!0}),e.editFeatureMeta.description="",e.descEditable=!1,e.descvisalble=!0,t.getFeatureMata())}))},handelCancel:function(){this.descEditable=!1,this.editCampaignMeta.description="",this.descvisalble=!0},handleEdit:function(){this.descEditable=!0,this.editFeatureMeta.description=this.featureMeta.description,this.descvisalble=!1},handleSubModelEdit:function(e,t){this.editFormVisible=!0,this.editForm=Object.assign({},t)},getFeatureMata:function(){var e=this,t={feature_id:e.$route.params.feature_id};n.a.ajax({type:"get",url:o["I"]+"/api/features/get_feature_metadata",async:!0,data:t,headers:{Authorization:"Token "+JSON.parse(sessionStorage.getItem("token"))},timeout:5e3,success:function(t){"999999"===t.code?(e.featureMeta=t.data.data,console.log(e.featureMeta,"self.featureMeta")):e.$message.error({message:t.msg,center:!0})}})},handleAdd:function(){this.addFormVisible=!0},editSubmit:function(){var e=this,t=this;this.$refs.editForm.validate((function(a){a&&e.$confirm("确认提交吗？","提示",{}).then((function(){t.editLoading=!0;var e={name:t.editForm.name,version:t.editForm.version,status:t.editForm.status,description:t.editForm.description,user_name:JSON.parse(sessionStorage.getItem("name"))},a={"Content-Type":"application/json",Authorization:"Token "+JSON.parse(sessionStorage.getItem("token"))};Object(o["L"])(a,e).then((function(e){var a=e.msg,s=e.code;t.editLoading=!1,"999999"===s?(t.$message({message:"修改成功",center:!0,type:"success"}),t.$refs["editForm"].resetFields(),t.editFormVisible=!1,t.getFeatureModelList()):t.$message.error({message:a,center:!0})}))}))}))},addSubmit:function(){var e=this;this.$refs.addForm.validate((function(t){if(t){var a=e;e.$confirm("确认提交吗？","提示",{}).then((function(){a.addLoading=!0;var e=JSON.stringify({name:a.addForm.name,version:a.addForm.version,feature_id:a.$route.params.feature_id,description:a.addForm.description,user_name:JSON.parse(sessionStorage.getItem("name"))}),t={"Content-Type":"application/json",Authorization:"Token "+JSON.parse(sessionStorage.getItem("token"))};Object(o["l"])(t,e).then((function(e){var t=e.msg,s=e.code;a.addLoading=!1,"999999"===s?(a.$message({message:"添加成功",center:!0,type:"success"}),a.$refs["addForm"].resetFields(),a.addFormVisible=!1,a.getFeatureModelList()):"999997"===s?a.$message.error({message:t,center:!0}):(a.$message.error({message:t,center:!0}),a.$refs["addForm"].resetFields(),a.addFormVisible=!1,a.getFeatureModelList())}))}))}}))},handleChange:function(e){console.log(e)},LookExpDetails:function(e,t){var a=this;a.$router.push({name:"查看实验详情",params:{api_id:t.id}})},expandModelClick:function(e){this.getExpAltList(e.id)},getFeatureModelList:function(){this.listLoading=!0;var e=this;n.a.ajax({type:"get",url:o["I"]+"/api/features/get_feature_models",async:!0,data:{feature_id:this.$route.params.feature_id,page:e.page,name:e.filters.name,user_name:JSON.parse(sessionStorage.getItem("name"))},headers:{Authorization:"Token "+JSON.parse(sessionStorage.getItem("token"))},timeout:5e3,success:function(t){e.listLoading=!1,"999999"===t.code?(e.ModelList=t.data.data,e.total=t.data.total,console.log(e.ModelList,"self.Modellist")):e.$message.error({message:t.msg,center:!0})}})},handleDel:function(e,t){var a=this;this.$confirm("确认删除该模型信息吗?","提示",{type:"warning"}).then((function(){a.listLoading=!0;var e=a;n.a.ajax({type:"post",url:o["I"]+"/api/features/del_feature_model",async:!0,data:JSON.stringify({model_id:t.id,user_name:JSON.parse(sessionStorage.getItem("name"))}),headers:{"Content-Type":"application/json",Authorization:"Token "+JSON.parse(sessionStorage.getItem("token"))},timeout:5e3,success:function(t){"999999"===t.code?e.$message({message:"删除成功",center:!0,type:"success"}):e.$message.error({message:t.msg,center:!0}),e.getFeatureModelList()}})})).catch((function(){}))},getExpAltList:function(e){var t=this;n.a.ajax({type:"get",url:o["I"]+"/api/campaigns/case_exp_altlist",async:!0,data:{campaign_id:this.$route.params.campaign_id,ab_id:e},headers:{Authorization:"Token "+JSON.parse(sessionStorage.getItem("token"))},timeout:5e3,success:function(e){"999999"===e.code?t.altListData=e.data.data:t.$message.error({message:e.msg,center:!0})}})},handleCurrentChange:function(e){this.page=e,this.getFeatureModelList()}},mounted:function(){this.getFeatureMata(),this.getFeatureModelList(),this.getModelsList()}},m=c,u=(a("9fc2"),a("2877")),p=Object(u["a"])(m,s,i,!1,null,"089522ee",null);t["default"]=p.exports},"6f9c":function(e,t,a){},"9fc2":function(e,t,a){"use strict";a("6f9c")}}]);
//# sourceMappingURL=chunk-1c5c1167.67652c74.js.map