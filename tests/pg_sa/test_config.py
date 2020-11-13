import asyncio

from aiohttp_rest_framework import APP_CONFIG_KEY
from tests.config import db
from tests.pg_sa.app import get_app
from tests.pg_sa.utils import create_db, drop_db


def setup_module():
    loop = asyncio.new_event_loop()
    loop.run_until_complete(create_db(db_name=db["database"]))
    loop.close()


def teardown_module():
    loop = asyncio.new_event_loop()
    loop.run_until_complete(drop_db(db_name=db["database"]))
    loop.close()


async def test_config_app_connection_property(aiohttp_client):
    apc = "engine"
    rest_config = {"app_connection_property": apc}
    app = get_app(rest_config)
    await aiohttp_client(app)  # instantiate here client so `on_startup` signal fires
    cfg = app[APP_CONFIG_KEY]
    assert cfg.app_connection_property == apc, "connection property wasn't applied in settings"
    assert await cfg.get_connection()
