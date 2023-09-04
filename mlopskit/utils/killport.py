import os


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
