import os

__version__ = "2.0.2"


def kill9_byname(strname):
    """
    kill -9 process by name
    """
    fd_pid = os.popen(
        "ps -ef | grep -v grep |grep %s \
            |awk '{print $2}'"
        % (strname)
    )
    pids = fd_pid.read().strip().split("\n")
    fd_pid.close()
    for pid in pids:
        os.system("kill -9 %s" % (pid))


def kill9_byport(strport):
    """
    kill -9 process by name
    """
    fd_pid = os.popen(
        "lsof -i:%s \
            |awk '{print $2}'"
        % (strport)
    )
    pids = fd_pid.read().strip().split("\n")
    fd_pid.close()
    # print(pids)
    for pid in pids:
        if pid != "PID":
            os.system("kill -9 %s" % (pid))
