from mlopskit.pipe import ServiceMgr
from mlopskit import Client

test = ServiceMgr(["{{model_name}}"], env="dev")
test.start_service()

test.scan_logs(100000)


Client(port=4001).predict(payload)
Client(port=5001).predict(payload, "predict/rewardserver")
