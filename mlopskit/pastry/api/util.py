from typing import Callable, Optional, Union
from pathlib import Path
import subprocess
import psutil

import os
from .template import (
    README,
    MAKEFILE,
    RECOMSERVER,
    REWARDSERVER,
    KILLPORT,
    RUN_RECOM,
    RUN_REWARD,
)

PathLike = Union[str, os.PathLike]


def kill_process_by_name(process_name):
    p1 = subprocess.Popen(["ps", "-A"], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(
        ["grep", process_name],
        stdin=p1.stdout,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    p3 = subprocess.Popen(
        ["awk", "{print $1}"],
        stdin=p2.stdout,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    pids, _ = p3.communicate()
    pids = [int(pid) for pid in pids.decode().split("\n") if pid]
    for pid in pids:
        try:
            proc = psutil.Process(pid)
            proc.kill()
            print(f"Killed process {pid} with name '{process_name}'")
        except psutil.NoSuchProcess:
            pass


def kill_process_by_port(port):
    p1 = subprocess.Popen(["lsof", "-i", f"TCP:{port}"], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(
        ["awk", "!/COMMAND/{print $2}"],
        stdin=p1.stdout,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    pids, _ = p2.communicate()
    pids = [int(pid) for pid in pids.decode().split("\n") if pid]
    for pid in pids:
        try:
            proc = psutil.Process(pid)
            proc.kill()
            print(f"Killed process {pid} listening on port {port}")
        except psutil.NoSuchProcess:
            pass


# kill_process_by_port(8080)


def create_file(path: PathLike, content: str, pretend=False, encoding="utf-8"):
    """Create a file in the given path.
    This function reports the operation in the logs.
    Args:
        path: path in the file system where contents will be written.
        content: what will be written.
        pretend (bool): false by default. File is not written when pretending,
            but operation is logged.
    Returns:
        Path: given path
    """
    path = Path(path)
    if not pretend:
        path.write_text(content, encoding=encoding)

    # logger.report("create", path)
    return path


def create_structure(project_main_dir, project_name, model_name, version):
    structure = {
        "README.md": {
            "content": README.substitute(new_proj=project_name),
            "is_dir": False,
        },
        "Makefile": {"content": MAKEFILE, "is_dir": False},
        "tests": {"content": "", "is_dir": True},
        "notebooks": {"content": "", "is_dir": True},
        "config": {"content": "", "is_dir": True},
        "db": {"content": "", "is_dir": True},
        "src/recomserver.py": {
            "content": RECOMSERVER.substitute(name=model_name, version=version),
            "is_dir": False,
            "rel_path": "src",
        },
        "src/rewardserver.py": {
            "content": REWARDSERVER.substitute(name=model_name, version=version),
            "is_dir": False,
            "rel_path": "src",
        },
        "bin/kill_recom.py": {"content": KILLPORT, "is_dir": False, "rel_path": "bin"},
        "bin/kill_reward.py": {"content": KILLPORT, "is_dir": False, "rel_path": "bin"},
        "bin/run_reward.sh": {
            "content": RUN_REWARD,
            "is_dir": False,
            "rel_path": "bin",
        },
        "bin/run_recom.sh": {"content": RUN_RECOM, "is_dir": False, "rel_path": "bin"},
    }
    for file_name, _content in structure.items():
        if _content.get("rel_path"):
            rel_path = _content.get("rel_path")
            content = _content.get("content")
            file_dir = os.path.join(project_main_dir, rel_path)
            os.makedirs(file_dir, exist_ok=True)
            create_file(os.path.join(project_main_dir, file_name), content)
        else:
            if _content.get("is_dir"):
                os.makedirs(os.path.join(project_main_dir, file_name), exist_ok=True)
            else:
                content = _content.get("content")
                create_file(os.path.join(project_main_dir, file_name), content)
