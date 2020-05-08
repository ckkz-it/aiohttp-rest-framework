import typing
from functools import partial

import aiopg.sa
from aiohttp import web

from aiohttp_rest_framework import APP_CONFIG_KEY
from tests.base_app import get_base_app
from tests.config import postgres_url


async def init_pg(app_conn_prop, app: web.Application) -> None:
    app[app_conn_prop] = await aiopg.sa.create_engine(postgres_url)


async def close_pg(app_conn_prop, app: web.Application) -> None:
    app[app_conn_prop].close()
    await app[app_conn_prop].wait_closed()


def get_app(rest_config: typing.Mapping = None):
    app = get_base_app(rest_config=rest_config)
    app_conn_prop = app[APP_CONFIG_KEY].app_connection_property
    app.on_startup.append(partial(init_pg, app_conn_prop))
    app.on_cleanup.append(partial(close_pg, app_conn_prop))
    return app
