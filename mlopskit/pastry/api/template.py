import string

readme_string = """\
# 机器学习项目-$new_proj


<h3 align="center">$new_proj</h3>


---


## 🧐 关于 <a name = "about"></a>

用于机器学习项目规范

## 🔖 项目结构

```
$new_proj/
|- bin/          # 包含可执行的的脚本和main文件
|- config/       # 配置文件
|- notebooks/    # 用于EDA探索和建模的的notebooks
|- secrets       # 包含api密钥和秘密参数。如果上传至git需要将该项隐藏或加入.gitignore文件
|- src/          # 源代码 - 包含核心功能
|- tests/        # 测试文件应该是src文件夹的镜像
|- Makefile      # 通过make utility使任务自动化
```

## 🏁 操作指南 <a name = "getting_started"></a>
这些说明将使你在本地机器上建立和运行一个项目的副本，目的是用于开发和测试。

### 克隆该项目
```
git clone https
```

## 设置你的环境并安装项目的依赖
```
conda create -n ml_template python=1.0
source activate ml_template


python -m pip install pip-tools
pip-compile --output-file requirements.txt requirements.in requirements_dev.in
python -m pip install -r requirements.txt
```

### 安装

## 🔧 运行测试
编写好的测试文件置于 ./tests 目录下， 你需要运行以下命令来执行它们。
```
make tests
```

## 🚀 部署
添加关于如何在实时系统（生产）上部署的附加说明。

## 🎈 贡献
如果团队成员想要在这个项目中做出贡献，请按照开始部分的步骤在本地设置该项目。

我们使用尽量少的包来保证高质量的代码。在提交之前，你可以运行：
使用 black 来格式化你的代码
```
make black
```
获得关于不符合pep8代码规范的预警信息：
（该命令会运行项目中的所有.py文件。）
```
make lint
```
你也可以自动运行black、lint和其他一些软件包，在提交前分析和检查你的代码库。

```
make precommit
```

##  ✍️ Authors
ml_template - leepand6@gmail.com"
"""

makefile_string = """\
TEST_PATH=./

.DEFAULT_GOAL := help

.PHONY: help precommit lint tests black ci killall

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'


.PHONY: precommit
precommit: ## Run all pre-commit hooks
	pre-commit run --all-file --show-diff-on-failure

.PHONY: lint
lint: ## Lint your code using pylint
	python -m pylint --version
	find . -type f -name "*.py" | xargs python -m pylint

.PHONY: tests
test: ## Run tests using pytest
	python -m pytest --version
	python -m pytest tests

.PHONY: black
black: ## Format your code using black
	python -m black --version
	python -m black .

## Run ci part
.PHONY: ci
ci: precommit tests

.PHONY: killall
killall: ## kill all server
		cd bin && python kill_recom.py && python kill_reward.py

.PHONY: killrecom
killrecom: ## kill recom server
		cd bin && python kill_recom.py

.PHONY: killreward
killreward: ## kill reward server
		cd bin && python kill_reward.py

.PHONY: ksrecom
ksrecom: ## kill and serve recom
		cd bin && python kill_recom.py && sh run_recom.sh

.PHONY: ksall
ksall: ## kill and serve recom/reward
		cd bin && python kill_recom.py && sh run_recom.sh && python kill_reward.py && sh run_reward.sh

.PHONY: ksreward
ksreward: ## kill and serve reward
		cd bin && python kill_reward.py && sh run_reward.sh
"""

recomserver_string = """\
from mlopskit.ext.store import YAMLDataSet
from mlopskit import Model, ModelLibrary, serving
from mlopskit.pastry.api import make
from mlopskit.pastry.data_store import Prediction
import traceback
import numpy as np
import random


class RecomServer(Model):
    CONFIGURATIONS = {"recomserver": {}}

    def _load(self):
        self.model_db = make("cache/$name-v$version",db_name="model.db")

    def _predict(self, items):
        return items


library = ModelLibrary(models=[RecomServer])

model = library.get("recomserver")

model_meta={'name': 'spinux_strategy_recom', 
    'recomserver_port':5000,
    'port': 5000, 
    'status': 
    'stoped'}
# spinux_strategy_recom : model name
make("meta/spinux_strategy_recom",meta_ops="set",meta_content=model_meta)

serving(
    [RecomServer],
    ["recomserver"],
    {"port": 5000, "workers": 4},
)
"""

rewardserver_string = """\
from mlopskit.ext.store import YAMLDataSet
from mlopskit import Model, ModelLibrary, serving
from mlopskit.pastry.api import make
from mlopskit.pastry.data_store import Prediction
import traceback
import numpy as np
import pickle



class RewardServer(Model):
    CONFIGURATIONS = {"rewardserver": {}}

    def _load(self):
        self.model_db = make("cache/$name-v$version",db_name="model.db")
        self.model_monotor_db = make(
            "db/$name-v$version"
            )

    def _predict(self, items):
        return items


library = ModelLibrary(models=[RewardServer])

model = library.get("rewardserver")

model_meta={'name': 'spinux_strategy_recom', 
    'rewardserver_port':6001,
    'port': 5000, 
    'status': 
    'stoped'}
# spinux_strategy_recom : model name
make("meta/spinux_strategy_recom",meta_ops="set",meta_content=model_meta)


serving(
    [RewardServer],
    ["rewardserver"],
    {"port": 6001, "workers": 4},
)
"""

kill_string = """\
import os

def kill9_byname(strname):
    fd_pid = os.popen(
        "ps -ef | grep -v grep |grep %s \
            |awk '{print $2}'"
        % (strname)
    )
    pids = fd_pid.read().strip().split("\n")
    fd_pid.close()
    for pid in pids:
        os.system("kill -9 %s" % (pid))


def kill9_byport(strport):
    fd_pid = os.popen(
        "lsof -i:%s \
            |awk '{print $2}'"
        % (strport)
    )
    pids = fd_pid.read().strip().split("\n")
    fd_pid.close()
    # print(pids)
    for pid in pids:
        if pid != "PID":
            os.system("kill -9 %s" % (pid))


kill9_byport("port")

"""
run_recomstring = """\
cd ../src && nohup python recomserver.py > ../logs/recom.log 2>&1 &
"""
run_rewardstring = """\
cd ../src && nohup python rewardserver.py > ../logs/reward.log 2>&1 &
"""

README = string.Template(readme_string)
MAKEFILE = makefile_string  # string.Template(makefile_string)
RECOMSERVER = string.Template(recomserver_string)
REWARDSERVER = string.Template(rewardserver_string)
KILLPORT = kill_string
RUN_RECOM = run_recomstring
RUN_REWARD = run_rewardstring
