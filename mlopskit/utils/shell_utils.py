import mlopskit.ext.shellkit as sh

import subprocess
import traceback
import os
import sys
import time

from structlog import get_logger

logger = get_logger(__name__)


def get_python_version():
    """
    :return: Current python version in 'major.minor.micro' format
    """
    major, minor, micro, *_ = sys.version_info
    return f"{major}.{minor}.{micro}"


def get_port_status(port):
    try:
        process = sh.cmd("lsof", "-i", f":{port}").run(preexec_fn=os.setsid)
        stdout = process.stdout
        stderr = process.stderr

        if "PID" in stdout:
            status = "running"
        else:
            status = "failed"

        if stderr:
            status = stderr.strip()

        return status
    except:
        e = str(traceback.format_exc())
        return f"Error: {e}"


def start_service(script, timeout=240):
    try:
        # 执行shell命令并捕获日志
        process = subprocess.run(
            f"{script}",
            shell=True,
            capture_output=True,
            preexec_fn=os.setsid,
            text=True,
            timeout=timeout,  # 设定超时时间
            check=True,  # 检查命令执行结果，若返回非零状态码则抛出异常
        )

        if process.stdout or process.stderr:
            msg = process.stderr.strip()
        else:
            msg = "your script is processed success"
            logger.debug(f"your script {script} is processed success")

        return msg
    except subprocess.CalledProcessError as e:
        return f"Error: {e}"
    except subprocess.TimeoutExpired:
        return "Command execution timed out"


def wait_until_port_used(port, max_wait_sec=15, interval_sec=0.5):
    """
    wait until the port is used.  *Notice this function will invoke\
    a bash shell to execute command [netstat]!*

    :return:
        return True if the port is used
    """
    curr_wait_sec = 0

    while curr_wait_sec < max_wait_sec:
        if get_port_status(port) == "running":
            return True
        curr_wait_sec += interval_sec
        time.sleep(interval_sec)
    return False
