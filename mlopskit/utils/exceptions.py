class UtilsError(Exception):
    """
    Super class of exceptions in utils module.
    """

    def __init__(self, error_info):
        self.error_info = "[MLOpskit Utils Error]: {}".format(error_info)


class SerializeError(UtilsError):
    """
    Serialize error raised by pyarrow.
    """

    def __init__(self, error_info):
        error_info = (
            "Serialize error, you may have provided an object that cannot be "
            + "serialized by pyarrow. Detailed error:\n{}".format(error_info)
        )
        super(SerializeError, self).__init__(error_info)

    def __str__(self):
        return self.error_info


class DeserializeError(UtilsError):
    """
    Deserialize error raised by pyarrow.
    """

    def __init__(self, error_info):
        error_info = (
            "Deserialize error, you may have provided an object that cannot be "
            + "deserialized by pyarrow. Detailed error:\n{}".format(error_info)
        )
        super(DeserializeError, self).__init__(error_info)

    def __str__(self):
        return self.error_info
