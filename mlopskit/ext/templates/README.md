# 机器学习项目模版

<p align="center">
  <a href="" rel="noopener">
 <img width=200px height=200px src="https://i.imgur.com/6wj0hh6.jpg" alt="Project logo"></a>
</p>

<h3 align="center">{model_name}</h3>


---


## 🧐 关于 <a name = "about"></a>

用于机器学习项目规范

## 🔖 项目结构

```
ml_template/
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
ml_template - leepand6@gmail.com