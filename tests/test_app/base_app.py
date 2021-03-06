import typing

from aiohttp import web

from aiohttp_rest_framework import setup_rest_framework
from tests.test_app.sa.orm.routes import setup_routes


def get_base_app(rest_config: typing.Mapping = None):
    base_app = web.Application()
    setup_routes(base_app)
    setup_rest_framework(base_app, rest_config)
    return base_app
