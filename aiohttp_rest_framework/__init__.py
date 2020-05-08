import typing

from aiohttp import web

from aiohttp_rest_framework.fields import patch_marshmallow_fields
from aiohttp_rest_framework.settings import Config, set_global_config

__version__ = "0.0.2a"

APP_CONFIG_KEY = "rest_framework"


def setup_rest_framework(app: web.Application, conf: typing.Mapping = None) -> None:
    user_settings = conf or {}
    app_settings = Config(app, **user_settings)
    app[APP_CONFIG_KEY] = app_settings

    set_global_config(app_settings)
    patch_marshmallow_fields()
