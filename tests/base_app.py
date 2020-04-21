from aiohttp import web

from aiohttp_rest_framework.settings import setup_rest_framework
from tests.routes import setup_routes


def get_base_app():
    base_app = web.Application()
    setup_routes(base_app)
    setup_rest_framework(base_app)
    return base_app
