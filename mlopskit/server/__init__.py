""" A flask application for hosting machine learning models. """
import os
from flask import Flask
from flask_cors import CORS
from flask_httpauth import HTTPBasicAuth
from mlflow.tracking import MlflowClient

# from server.config import config
from colorama import init
from .routes import ui_routes, path_to_local_sqlite_uri
from .models import SysModelInit
from mlopskit.ext.store.yaml.yaml_data import YAMLDataSet
from mlopskit.utils.file_utils import data_dir

from mlopskit.config import CONFIG

home_path = data_dir()
default_config = os.path.join(home_path, "mlops_config.yml")
default_config_exists = os.path.exists(os.path.join(home_path, "mlops_config.yml"))

if default_config_exists:
    config = YAMLDataSet(default_config).load()
    mlflow_url_local = config.get("mlflow_url_local")
    mlops_art_basepath = config.get("mlflow_art_path", os.getcwd())
    mlflow_client = MlflowClient(tracking_uri=mlflow_url_local)
    mlflow_local_server_uri = mlflow_url_local
    mlops_sqlite_db = config.get("mlops_sqlite_db")
else:

    mlflow_local_server_uri = CONFIG["mlflow_local_server_uri"]
    mlops_sqlite_db = CONFIG["mlops_sqlite_db"]
    mlops_art_basepath = CONFIG["mlops_art_basepath"]

defa_db_uri = path_to_local_sqlite_uri(mlops_sqlite_db)
sys_db_uri = os.environ.get("DATABASE_URL", defa_db_uri)

sql_db = SysModelInit(sys_db_uri)


if os.name == "nt":
    init(convert=True)

config_name = os.getenv("FLASK_CONFIG") or "default"
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__, static_url_path="")
app.register_blueprint(ui_routes, url_prefix="/")
# FlaskDB(app, db) #解决peewee不自动关闭连接池连接，参见https://www.cnblogs.com/xueweihan/p/6698456.html

# r'/*' 是通配符，让本服务器所有的 URL 都允许跨域请求
CORS(app, resources=r"/*")
CORS(app, supports_credentials=True)
app.config["SECRET_KEY"] = "hard to guess string"

# app.config.from_object(config[config_name])

auth = HTTPBasicAuth()
CSRF_ENABLED = True
app.debug = True

# import server.apps.settings
from .routes import login
from .routes import users
from .routes import campaign_registry
from .routes import dashboard
from .routes import model_tracking
from .routes import feature_store
