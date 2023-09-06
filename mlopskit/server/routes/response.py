from flask import jsonify


class Response(object):
    def success(self, data=[]):
        return jsonify({"code": "999999", "msg": "成功！", "data": data})

    def failed(self, msg=""):
        return jsonify({"code": "999998", "msg": "失败！错误信息：" + str(msg) + "，请联系管理员。"})

    def nopriv(self, msg=""):
        return jsonify({"code": "999983", "msg": "失败！错误信息：" + str(msg) + "，请联系管理员。"})

    def delprojfailed(self, msg=""):
        return jsonify({"code": "999995", "msg": "失败！错误信息：" + str(msg) + "，请联系管理员。"})
