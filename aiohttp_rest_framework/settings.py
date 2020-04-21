import typing

from aiohttp import web

from aiohttp_rest_framework.db import AioPGService, DatabaseServiceABC


class Config:
    def __init__(
            self,
            app: web.Application,
            *,
            connection: typing.Any = None,
            app_connection_property: str = "db",
            get_connection: typing.Callable = None,
            db_service: typing.Type[DatabaseServiceABC] = AioPGService,
    ):
        def _get_connection():
            return connection or app[app_connection_property]

        self.get_connection = get_connection or _get_connection
        assert callable(self.get_connection), "`get_connection` has to be callable"
        self.db_service_class = db_service


APP_CONFIG_KEY = "rest_framework"

config = None


def setup_rest_framework(app: web.Application, settings: typing.Mapping = None) -> None:
    user_settings = settings or {}
    app_settings = Config(app, **user_settings)
    app[APP_CONFIG_KEY] = app_settings

    global config
    config = app_settings
