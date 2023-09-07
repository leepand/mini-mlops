<h1 align="center"><a href="https://github.com/leepand/open-mlops">mlopskit</a></h1>
<p align="center">
  <em>MLOps for (online) machine/reinforcement learning</em>
</p>

---

<p align="center">
  <a href="https://github.com/leepand/mini-mlops"><img src="https://img.shields.io/github/license/leepand/mini-mlops" /></a>
  <a href="https://github.com/leepand/mini-mlops"><img src="https://img.shields.io/github/issues/leepand/mini-mlops" /></a>
   <a href="https://github.com/leepand/mini-mlops"><img src="https://img.shields.io/github/watchers/leepand/mini-mlops" /></a> 
  <a href="https://github.com/leepand/mini-mlops"><img src="https://img.shields.io/github/forks/leepand/mini-mlops" /></a>    
   <a href="https://github.com/leepand/mini-mlops"><img src="https://img.shields.io/github/stars/leepand/mini-mlops" /></a>   
   <a href="https://github.com/leepand/mini-mlops"><img src="https://img.shields.io/github/commit-activity/m/leepand/mini-mlops" /></a>   
   
</p>

`mlopskit` 是一个简约而功能齐全的从0-1的 MLOps 项目，专为想要将ML模型部署到生产环境的数据科学家或算法工程师而构建的，旨在使数据科学家们开发的 ML 模型可重用、健壮、高性能且易于部署，适应于中小型企业的 MLOps 实践参考。

我们希望提供一款极简风的MLOps，它可以处理无聊的事情，可以嵌入现有系统，并且使用起来很有趣。

## 特性

将您的预测代码包装在`mlopskit`中可以立即继承以下功能：
- **Online-first：** 专为在线机器学习/强化学习模型而设计，同时也支持批处理。
- **可组合：** 模型可以依赖于其他模型，并根据需要评估它们
- **类型安全：** 模型的输入和输出可以通过[pydantic](https://pydantic-docs.helpmanual.io/)进行验证，你可以为你的预测获得类型注释，并且可以在开发过程中用静态类型分析工具捕捉错误。
- **异步：** 模型支持异步和同步的预测功能。`mlopskit`支持从同步代码中调用异步代码，这样你就不必受部分异步代码的影响。
- **可测试：** 模型携带自己的单元测试案例，单元测试使用[pytest](https://docs.pytest.org/en/6.2.x/)框架。
- **快速部署：** 模型可以通过使用[fastapi](https://fastapi.tiangolo.com/)在单个CLI调用中提供。
- **协作化：** 可以将你的ML库和工件以Python包或服务的形式与他人分享。让其他人使用和评估你的模型
- **快速编码：** 只需编写业务和模型逻辑，就可以了。没有繁琐的前处理或后处理逻辑、分支选项等。
- **支持批量测测：** 可以以最小的开销对模型预测进行批处理（可以自定义批处理逻辑）

## 🤱 快速开始

启动服务:

```
mlopskit run -s all --backend true
```

服务运行成功日志:

```sh
2023-09-07 16:58:06 [info     ] mlopskit config file mlops_config.yml! path=/Users/leepand/.mlopskit/mlops_config.yml
2023-09-07 16:58:06 [debug    ] your script sh run.sh is processed success
2023-09-07 16:58:06 [info     ] stdout info: your script is processed success! name=mlflow service serving
2023-09-07 16:58:06 [debug    ] your script nohup sh run_model_server.sh > run_model_server.log 2>&1 & is processed success
2023-09-07 16:58:06 [info     ] stdout info: your script is processed success! name=model server service serving
2023-09-07 16:58:06 [debug    ] your script nohup gunicorn --workers=3 -b 0.0.0.0:8080  mlopskit.server.wsgi:app >main_server.log 2>&1 & is processed success
2023-09-07 16:58:06 [info     ] serving ui info: your script is processed success! name=main service serving
```

创建新项目（模型）:

项目名称-mlops_new_proj，模型名称-new_model，模型版本-2:

```
mlopskit init -p mlops_new_proj -m new_model -v 2
# 创建成功日志：
# 2023-09-07 16:43:28 [info     ] Project mlops_new_proj is created! name=mlops_new_proj
```

模型注册：

```
mlopskit regmodel --name new_model --filesdir mlops_new_proj
```

模型注册成功日志示例：

```bash
Confirm register model new_model files to remote repository (y/n)y
2023-09-07 17:23:26 [info     ] APIs of mlopskit               model_name=new_model model_version=None ops_type=model
2023-09-07 17:23:26 [info     ] The list of all versions for the current model is [1, 2, 3, 4].
2023-09-07 17:23:26 [warning  ] Using the latest versioned model `4` instead of the unversioned model `None`.If you insist on doing so, we will create a new version `5` for you.
2023-09-07 17:23:26 [info     ] Usage of mlopskit-model        Params={'ops_type': 'push/pull/serving/predict/killservice/serving_status, default:push'}
2023-09-07 17:23:26 [info     ] Usage of mlopskit-push         Params={'to_push_file': 'model file/dir to upload to remote model space', 'push_type': 'file/pickle, default: file'}
2023-09-07 17:23:26 [info     ] Usage of mlopskit-pull         Params={'save_path': 'local path to download model'}
2023-09-07 17:23:27 [info     ] model version 5 is created!
```

模型部署

`mlopskit`使用mlflow进行模型实验的跟踪、模型注册等功能，并提供了一种直接且一致的方式来将预测代码封装在一个Model类中：

```
from mlopskit import Model,serving
import numpy as np
from sklearn.datasets import load_diabetes
from sklearn.linear_model import LinearRegression

X, y = load_diabetes(return_X_y=True)

lr = LinearRegression()
lr.fit(X, y)


class LrModel(Model):
    CONFIGURATIONS = {"lrmodel":{}}
    def _predict(self,items):
        request_id = items.get("request_id")
        xx= np.array(items.get("x")).reshape(1,-1)
        return {"result":lr.predict(xx).tolist()[0]}
    

serving([LrModel],["lrmodel"],{"port":9000})

## 接口测试
%%time
import sys

import requests


def main():

    payload = {"x":X[0].tolist()}
    r = requests.post('http://localhost:9000/predict/lrmodel', json=payload)
    r.raise_for_status()
    print(r.json())




if __name__ == '__main__':
    main()
```

## 技术架构

<img src="resources/art.png">

## Documentation
使用范例可在[docs](docs)文件夹中找到。

- [客户端使用](docs/mlops-client.md)
    - [客户端配置](docs/mlops-client.md#settings)
- [模型实验跟踪](docs/mlops-tracking.md)
    - [Experiment](docs/mlops-tracking.md#experiment)
    - [Run](docs/mlops-tracking.md#run)
    - [Run Metrics](docs/mlops-tracking.md#run-metrics)
    - [Model](docs/mlops-tracking.md#model)
    - [Model version](docs/mlops-tracking.md#model-version)
- [模型部署](docs/mlops-deploy.md)
    - [Push Model](docs/mlops-deploy.md#push-model)
    - [Pull Model](docs/mlops-deploy.md#pull-model)
- [模型服务化](docs/mlops-serving.md)
    - [Serving Model](docs/mlops-serving.md#serving-model)
    - [Serving Model Status](docs/mlops-serving.md#serving-model-status)
- [数据存储](docs/mlops-data-store.md)
    - [日志存储](docs/mlops-data-store.md#events-record)
    - [模型存储](docs/mlops-data-store.md#model-store)
    - [特征存储](docs/mlops-data-store.md#feature-store)

## 🌳 updated 2.0.1

step1:

mlopskit init -p $v$x

如果是新版本，需要 eg. mlopskit regmodel --name some_model --filesdir $v$x

编辑config/server_xx.yml配置：

ops_servers: type：list，需要服务的代码文件名
文件名作为key：

step2:
将模型上传至共享repo，默认为dev环境（对应config/server_dev.yml），mlopskit push --pipe some_model --filename v1 --preview
如果上传至生产repo（需要编写config/server_prod.yml，注意端口是否占用），mlopskit push --pipe some_model --filename v1 --profile prod --preview

step3:
服务化：
```python
from mlopskit.pipe import ServiceMgr
test=ServiceMgr(["some_model"],env="dev") # 如果生产环境，则env="prod"
test.start_service()
test.scan_logs()
```

## 相关资源
* [MLOps-机器学习从开发到生产](https://github.com/leepand/MLOps-practice)<br/>
