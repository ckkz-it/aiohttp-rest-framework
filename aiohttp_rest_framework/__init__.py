from typing import Mapping

from aiohttp import web

from aiohttp_rest_framework.fields import patch_marshmallow_fields
from aiohttp_rest_framework.settings import Config, set_global_config
from aiohttp_rest_framework.utils import create_connection  # noqa

__version__ = "0.0.5"

APP_CONFIG_KEY = "rest_framework"

__all__ = (
    "__version__",
    "APP_CONFIG_KEY",
    "setup_rest_framework",
    "create_connection",
)


def setup_rest_framework(app: web.Application, conf: Mapping = None) -> None:
    user_settings = conf or {}
    app_config = Config(app, **user_settings)
    app[APP_CONFIG_KEY] = app_config
    set_global_config(app_config)
    patch_marshmallow_fields()
