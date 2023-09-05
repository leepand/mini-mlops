import os
import json


def debug_log(items, model_name, debug_db, logs_debug, request_id):
    debug_key = f"{model_name}:debug"
    debug_param = debug_db.get(debug_key)

    # 检查是否设置了调试参数
    if debug_param == "1":
        debug_log_file = os.path.join(logs_debug, f"{request_id}_params.txt")
        # 将请求参数写入调试日志文件
        with open(debug_log_file, "w") as f:
            f.write(json.dumps(items))
