from .server.models.models import SUsers
from .server.models import database
from .server.routes import path_to_local_sqlite_uri
import os
from .utils.file_utils import data_dir

home_path = data_dir()
sql_db = os.path.join(home_path, "mlflow_workspace/mlops_meta.sqlite")
defa_db_uri = path_to_local_sqlite_uri(sql_db)
sys_db_uri = os.environ.get("DATABASE_URL", defa_db_uri)
sql_db = database.SysModelInit(sys_db_uri)

import datetime


def create_user(
    name="leepand", mobile="13370151381", password="123", email="pandeng.li@163.com"
):
    obj = SUsers(
        name=name,
        mobile=mobile,
        password=password,
        email=email,
        creation_date=datetime.datetime.utcnow(),
    )

    sql_db._create_object(obj)
    return True
