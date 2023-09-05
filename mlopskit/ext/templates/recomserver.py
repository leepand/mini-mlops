from mlopskit.ext.store.yaml.yaml_data import YAMLDataSet
from mlopskit import Model, ModelLibrary, make
from mlopskit.log_base import create_log_path

import traceback
import numpy as np
import os
import json

from utils import debug_log


class RecomServer(Model):
    CONFIGURATIONS = {"recomserver": {}}

    def _load(self):
        # 创建日志路径
        self.reocm_logs_path = create_log_path("{{model_name}}", "recom_errors")
        self.recom_logs_debug = create_log_path("{{model_name}}", "recom_debugs")
        self.debug_db = make("cache/feature_store-v1", db_name="debug_tests.db")

        self.model_db = make(
            "cache/{{model_name}}-v{{version}}", db_name="{{model_name}}.db"
        )

    def _predict(self, items):
        uid = items.get("uid")
        request_id = items.get("request_id")
        try:
            debug_log(
                items=items,
                model_name="{{model_name}}",
                debug_db=self.debug_db,
                logs_debug=self.recom_logs_debug,
                request_id=request_id,
            )

            return items
        except:
            # 将异常堆栈信息写入错误日志文件
            log_file = os.path.join(self.recom_logs_path, f"{request_id}_error.txt")
            with open(log_file, "w") as f:
                f.write(str(traceback.format_exc()))

            return items


library = ModelLibrary(models=[RecomServer])

model = library.get("recomserver")
