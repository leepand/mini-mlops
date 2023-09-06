class BaseError(Exception):
    """
    General BaseError error
    """


class MetadataError(BaseError):
    """
    General Metadata Error
    """


class UnknownMetadataError(MetadataError):
    def __init__(self):
        super(UnknownMetadataError, self).__init__(
            "Unknown error during query execution"
        )
