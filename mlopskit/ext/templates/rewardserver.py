from mlopskit.ext.store.yaml.yaml_data import YAMLDataSet
from mlopskit import Model, ModelLibrary, serving, make
from mlopskit.log_base import create_log_path

import traceback
import numpy as np
import json
import os

from utils import debug_log


class RewardServer(Model):
    CONFIGURATIONS = {"rewardserver": {}}

    def _load(self):
        self.reward_logs_path = create_log_path("{{model_name}}", "reward_errors")
        self.reward_logs_debug = create_log_path("{{model_name}}", "reward_debugs")
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
                logs_debug=self.reward_logs_debug,
                request_id=request_id,
            )

            return items
        except:
            # 将异常堆栈信息写入错误日志文件
            log_file = os.path.join(self.reward_logs_path, f"{request_id}_error.txt")
            with open(log_file, "w") as f:
                f.write(str(traceback.format_exc()))

            return items


library = ModelLibrary(models=[RewardServer])

model = library.get("rewardserver")
