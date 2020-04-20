import typing

from aiohttp import web

from aiohttp_rest_framework.db import AioPGService, DatabaseServiceABC


class Config:
    def __init__(
            self,
            app: web.Application,
            *,
            connection: typing.Any = None,
            db_service: typing.Type[DatabaseServiceABC] = AioPGService,
    ):
        self.connection = connection or app["db"]
        self.db_service_class = db_service


APP_CONFIG_KEY = "rest_framework"

config = None


def setup_rest_framework(app: web.Application, settings: typing.Mapping = None) -> None:
    user_settings = settings or {}
    app_settings = Config(app, **user_settings)
    app[APP_CONFIG_KEY] = app_settings

    global config
    config = app_settings
