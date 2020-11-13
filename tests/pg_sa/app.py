import typing
from functools import partial

from aiohttp import web

from aiohttp_rest_framework import APP_CONFIG_KEY, create_connection
from tests.base_app import get_base_app
from tests.config import db_url


async def init_pg(app_conn_prop, app: web.Application) -> None:
    app[app_conn_prop] = await create_connection(db_url)
    await app[app_conn_prop].connect()


async def close_pg(app_conn_prop, app: web.Application) -> None:
    await app[app_conn_prop].disconnect()


def get_app(rest_config: typing.Mapping = None):
    app = get_base_app(rest_config=rest_config)
    app_conn_prop = app[APP_CONFIG_KEY].app_connection_property
    app.on_startup.append(partial(init_pg, app_conn_prop))
    app.on_cleanup.append(partial(close_pg, app_conn_prop))
    return app
