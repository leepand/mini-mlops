"""该模块提供了一组辅助函数，用于在mlopskit包的同组件中使用。
"""
import importlib
from typing import Any


def load_obj(obj_path: str, default_obj_path: str = "") -> Any:
    """从一个给定的路径中提取一个对象。
    Args:
        obj_path: 要提取的对象的路径，包括对象名称。
        default_obj_path: 默认的对象路径。
    Returns:
        被提取的对象。
    Raises:
        AttributeError: 当该对象没有给定的命名属性时。
    """
    obj_path_list = obj_path.rsplit(".", 1)
    obj_path = obj_path_list.pop(0) if len(obj_path_list) > 1 else default_obj_path
    obj_name = obj_path_list[0]
    module_obj = importlib.import_module(obj_path)
    if not hasattr(module_obj, obj_name):
        raise AttributeError(f"Object '{obj_name}' cannot be loaded from '{obj_path}'.")
    return getattr(module_obj, obj_name)
