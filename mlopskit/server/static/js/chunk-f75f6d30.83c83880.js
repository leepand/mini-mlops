(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["chunk-f75f6d30"],{1048:function(t,e,a){"use strict";a("f28d")},"2e9f":function(t,e,a){},"9c39":function(t,e,a){"use strict";a("2e9f")},b7b4:function(t,e,a){"use strict";a.r(e);var n=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("section",{staticStyle:{"margin-left":"15px","margin-right":"15px","margin-top":"15px"}},[a("div",{staticClass:"index-container"},[a("el-row",{staticStyle:{"margin-top":"10px"},attrs:{gutter:20}},[a("el-col",{attrs:{xs:24,sm:24,md:24,lg:24,xl:24}},[t.noticeList[0]?a("el-alert",{attrs:{closable:t.noticeList[0].closable}},[a("div",{staticStyle:{display:"flex","align-items":"center","justify-content":"center"}},[a("a",{attrs:{target:"_blank",href:"https://github.com/chuzhixin/vue-admin-better"}}),a("p",{domProps:{innerHTML:t._s(t.noticeList[0].title)}})])]):t._e()],1),t._l(t.iconList,(function(e,n){return a("el-col",{key:n,staticStyle:{"margin-bottom":"10px"},attrs:{span:6}},[a("router-link",{attrs:{to:e.link}},[a("el-card",{staticClass:"icon-panel",attrs:{shadow:"never"}},[a("span",[a("strong",[t._v(t._s(e.cnt))])]),a("p",[t._v(t._s(e.title))])])],1)],1)})),a("el-col",{attrs:{xs:24,sm:24,md:24,lg:11,xl:11}},[a("el-card",{staticClass:"card",attrs:{shadow:"never"}},[a("div",{attrs:{slot:"header"},slot:"header"},[a("span",[t._v("依赖信息")]),a("div",{staticStyle:{float:"right"}},[t._v("部署时间:"+t._s(t.updateTime))])]),a("table",{staticClass:"table",attrs:{"header-align":"center"}},[a("tr",[a("td",[t._v("mlopskit")]),a("td",[t._v("MLOps组件")]),a("td",[t._v("CacheDB")]),a("td",[t._v("模型参数缓存库")])]),a("tr",[a("td",[t._v("ModelLibrary")]),a("td",[t._v("模型资产管理组件")]),a("td",[t._v("serving")]),a("td",[t._v("模型服务化组件")])]),a("tr",[a("td",[t._v("abkit")]),a("td",[t._v("A/B实验组件")]),a("td",[t._v("BoleRLrec")]),a("td",[t._v("强化学习库")])])])]),a("el-card",{attrs:{shadow:"never"}},[a("div",{attrs:{slot:"header"},slot:"header"},[a("span",[t._v("其他信息")])]),a("div",{staticStyle:{"text-align":"center"}},[a("vab-colorful-icon",{staticStyle:{"font-size":"140px"},attrs:{"icon-class":"vab"}}),a("h1",{staticStyle:{"font-size":"30px"}},[t._v("核心模块")])],1),t._l(t.noticeList,(function(e,n){return a("div",{key:n},[0!==n?a("el-alert",{attrs:{title:e.title,type:e.type,closable:e.closable}}):t._e(),a("br")],1)})),a("el-alert",{attrs:{closable:!1,title:t.userAgent,type:"info"}}),a("br")],2),a("version-information",{staticStyle:{"margin-top":"15px"}})],1),a("el-col",{attrs:{xs:24,sm:24,md:13,lg:13,xl:13}},[a("el-card",{staticClass:"card",attrs:{shadow:"never"}},[a("div",{attrs:{slot:"header"},slot:"header"},[a("span",[t._v("更新日志")])]),a("el-timeline",{attrs:{reverse:t.reverse}},t._l(t.activities,(function(e,n){return a("el-timeline-item",{key:n,attrs:{timestamp:e.timestamp,color:e.color}},[t._v("\n              "+t._s(e.content)+"\n            ")])})),1)],1),a("plan",{staticStyle:{"margin-top":"15px"}})],1)],2)],1)])},i=[],s=(a("96cf"),a("3b8d")),r=(a("7f7f"),a("4ec3")),c=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("el-card",{attrs:{shadow:"hover"},scopedSlots:t._u([{key:"header",fn:function(){return[a("vab-icon",{attrs:{icon:"send-plane-2-line"}}),a("el-tag",{staticClass:"card-header-tag",attrs:{type:"success"}},[t._v("\n      愿博乐数智平台和业务走上个性化智能的不归路。\n    ")])]},proxy:!0}])},[a("el-table",{attrs:{data:t.tableData,"row-key":"title",height:"283px"}},[a("el-table-column",{attrs:{align:"center",label:"专注",width:"50px"},scopedSlots:t._u([{key:"default",fn:function(t){return[a("i",{staticClass:"el-icon-milk-tea"})]}}])}),a("el-table-column",{attrs:{width:"20px"}}),a("el-table-column",{attrs:{prop:"title",label:"目标",width:"230px"}}),a("el-table-column",{attrs:{label:"进度",width:"220px"},scopedSlots:t._u([{key:"default",fn:function(t){var e=t.row;return[a("el-progress",{attrs:{percentage:e.percentage,color:e.color}})]}}])}),a("el-table-column",{attrs:{width:"70px"}}),a("el-table-column",{attrs:{prop:"endTIme",label:"完成时间"}})],1)],1)},o=[],l={data:function(){return{tableData:[{title:"实现活APA提升2%",endTIme:"2023-12-31",percentage:30,color:"#95de64"},{title:"实现总付费提升5%",endTIme:"2023-12-31",percentage:10,color:"#69c0ff"},{title:"实现BoleRLRec-V2.0强化学习框架",endTIme:"2023-12-31",percentage:30,color:"#1890FF"},{title:"完善MLOps组件",endTIme:"2023-12-31",percentage:50,color:"#ffc069"},{title:"升级博乐数智能平台",endTIme:"2023-12-31",percentage:16,color:"#5cdbd3"},{title:"变成像ChatGPT一样优秀的智能平台",endTIme:"此生无望",percentage:1,color:"#b37feb"}]}},mounted:function(){}},d=l,p=a("2877"),m=Object(p["a"])(d,c,o,!1,null,null,null),u=m.exports,f=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("el-card",{staticClass:"version-information",attrs:{shadow:"hover"},scopedSlots:t._u([{key:"header",fn:function(){return[a("vab-icon",{attrs:{icon:"information-line"}})]},proxy:!0}])},[a("el-scrollbar",[a("table",{staticClass:"table"},[a("tr",[a("td",[t._v("全局定价模型")]),a("td",[t._v("A2C/PPO")]),a("td",[t._v("个性化体验模型")]),a("td",[t._v("决策网络&评估网络")])]),a("tr",[a("td",[t._v("全局模型")]),a("td",[t._v("玩家共享Agent")]),a("td",[t._v("局部模型")]),a("td",[t._v("玩家独立的Agent")])]),a("tr",[a("td",[t._v("监督学习")]),a("td",[t._v("学习偏好和分群")]),a("td",[t._v("强化学习")]),a("td",[t._v("给出决策和优化决策")])]),a("tr",[a("td",[t._v("学习资源")]),a("td",{attrs:{colspan:"3"}},[a("a",{attrs:{target:"_blank",href:"https://github.com/AlgoLink/BoleRLrec"}},[a("el-button",{staticStyle:{"margin-left":"10px"},attrs:{type:"primary"}},[t._v("\n              BoleRLRec-V2.0\n            ")])],1),a("a",{attrs:{target:"_blank",href:"https://github.com/leepand/open-mlops"}},[a("el-button",{staticStyle:{"margin-left":"10px"},attrs:{type:"primary"}},[t._v("\n              open-mlops\n            ")])],1),a("a",{attrs:{href:"http://52.13.247.92:8901/",target:"_blank"}},[a("el-button",{staticStyle:{"margin-left":"10px"},attrs:{type:"warning"}},[t._v("\n              知识库\n            ")])],1)])])])])],1)},b=[],v={data:function(){return{}}},_=v,h=(a("9c39"),Object(p["a"])(_,f,b,!1,null,"06f2f378",null)),g=h.exports,y={name:"Index",components:{Plan:u,VersionInformation:g},data:function(){return{timer:0,updateTime:" 2023-01-31",nodeEnv:"production",dependencies:[],devDependencies:[],reverse:!0,activities:[],noticeList:[],userAgent:navigator.userAgent,iconList:[{icon:"el-icon-video-camera",title:"已建活动数",link:"/campaigns",cnt:"3",color:"#ffc069"},{icon:"table",title:"进行中的实验数",link:"/campaigns",cnt:"6",color:"#5cdbd3"},{icon:"laptop-code",title:"已注册的模型数",link:"/models",cnt:"5",color:"#b37feb"},{icon:"laptop-code",title:"模型版本数",link:"/models",cnt:"10",color:"#b37feb"}]}},created:function(){this.fetchData()},beforeDestroy:function(){clearInterval(this.timer)},mounted:function(){this.getModelMData(),new Schart("canvas",this.options)},methods:{getModelMData:function(){var t=this,e={user_name:JSON.parse(sessionStorage.getItem("name"))},a={"Content-Type":"application/json",Authorization:"Token "+JSON.parse(sessionStorage.getItem("token"))};Object(r["s"])(a,e).then((function(e){var a=e.msg,n=e.code,i=e.data;"999999"===n?(t.iconList=i,console.log(t.iconList,"self.iconList")):t.$message.error({message:a,center:!0})}))},handleClick:function(t){this.$baseMessage("点击了".concat(t.name,",这里可以写跳转"))},handleZrClick:function(t){},handleChangeTheme:function(){this.$baseEventBus.$emit("theme")},fetchData:function(){var t=Object(s["a"])(regeneratorRuntime.mark((function t(){var e,a,n,i;return regeneratorRuntime.wrap((function(t){while(1)switch(t.prev=t.next){case 0:return e={code:200,msg:"",data:[{_id:"60fd6dbecd84d60001f99f33",content:"设计与搭建BoleRLRec-V2.0框架。",timestamp:"2023-01-05"},{_id:"60fd6defcd84d60001f9a039",content:"实现在线 expected_sarsa 算法与agent",timestamp:"最近更新"},{_id:"610978795c2db80001a09dc5",content:"设计与实现actor网络-PolicyNetwork",timestamp:"最近更新"},{_id:"6117518b7c33d50001d1ab10",content:"设计与实现critic网络-StateValueNetwork",timestamp:"最近更新"},{_id:"612e2ecb1b51d10001b8f1ad",content:"设计与实现RL项目通用模版-mlopskit init",timestamp:"最近更新"},{_id:"61b6e72cd00c060001339c27",content:"设计与实现actor网络优化器-policy_optimizer",timestamp:"最近更新"},{_id:"61c4752c39bf1000016e4439",content:"设计与实现critic网络优化器-stateval_optimizer",timestamp:"最近更新"},{_id:"621ce37f3da49e0001b419b1",content:"设计A2C Agent基类",timestamp:"最近更新"},{_id:"6252ef47eb124700019b4977",content:"设计A2C在线参数存储与加载机制",timestamp:"最近更新"},{_id:"63874f37ce2777000176d727",content:"实现A2C算法与agent",timestamp:"2023-01-30"}]},t.next=3,e;case 3:a=t.sent,n=a.data,n.map((function(t,e){e===n.length-1&&(t.color="#0bbd87")})),this.activities=n,i={code:200,msg:"",data:[{_id:"60fd73529b33ed00017eac32",title:"\n\t博乐数智平台是基于强化学习的智能平台，我们的目标是持续提升玩家的个性化体验和付费。\n\t<a href='http://52.13.247.92:8901/' target='_blank'>知识沉淀</a>",closable:!1,type:"success"},{_id:"60fd737c2e5faa0001bb74ad",title:"MLOps：营销策略实验集市、模型实验跟踪及模型运营中心-模型及版本管理。",closable:!1,type:"warning"},{_id:"60fd73a33a9af40001fb586b",title:"BoleRLRec-V2.0：与MLOps兼容并异构的在线强化学习框架，统一的项目模版、可以在线实时更新模型参数以支持策略的决策。",closable:!0,type:"success"}]},this.noticeList=i.data;case 9:case"end":return t.stop()}}),t,this)})));function e(){return t.apply(this,arguments)}return e}()}},x=y,k=(a("1048"),Object(p["a"])(x,n,i,!1,null,"9dba378e",null));e["default"]=k.exports},f28d:function(t,e,a){}}]);
//# sourceMappingURL=chunk-f75f6d30.83c83880.js.map