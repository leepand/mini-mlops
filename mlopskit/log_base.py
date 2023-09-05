from mlopskit import make
import os


def create_log_path(model_name, logdir_name, if_center=True):
    if if_center:
        center_config = make("config/center")
        center_logs_path = center_config["center_logs_path"]
        _logs_path = os.path.join(center_logs_path, model_name, logdir_name)
    else:
        center_logs_path = "../logs"
        _logs_path = os.path.join(center_logs_path, logdir_name)

    os.makedirs(_logs_path, exist_ok=True)

    return _logs_path
