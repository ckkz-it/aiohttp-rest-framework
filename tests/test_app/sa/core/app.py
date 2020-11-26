import typing
from functools import partial

from aiohttp import web

from aiohttp_rest_framework import APP_CONFIG_KEY, create_connection
from tests.test_app.base_app import get_base_app


async def init_db(app_conn_prop: str, db_url: str, app: web.Application) -> None:
    app[app_conn_prop] = await create_connection(db_url)


async def close_db(app_conn_prop: str, app: web.Application) -> None:
    await app[app_conn_prop].dispose()


def create_application(db_url: str, rest_config: typing.Mapping = None):
    app = get_base_app(rest_config=rest_config)
    app_conn_prop = app[APP_CONFIG_KEY].app_connection_property
    app.on_startup.append(partial(init_db, app_conn_prop, db_url))
    app.on_cleanup.append(partial(close_db, app_conn_prop))
    return app
