from abc import ABCMeta


class Dam(metaclass=ABCMeta):  # (pydantic.BaseSettings):
    def __init__(self):
        self.model_store = None
        self.data_store = None

    @property
    def http_server(self):
        from .api.server import api, Settings, get_settings

        def get_settings_override():
            return Settings(dam=self)

        api.dependency_overrides[get_settings] = get_settings_override

        return api
