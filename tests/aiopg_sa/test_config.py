from aiohttp_rest_framework import APP_CONFIG_KEY
from tests.aiopg_sa.app import get_app
from tests.aiopg_sa.utils import create_pg_db, drop_pg_db
from tests.config import db


def setup_module():
    create_pg_db(db_name=db["database"])


def teardown_module():
    drop_pg_db(db_name=db["database"])


async def test_config_app_connection_property(aiohttp_client):
    apc = "engine"
    rest_config = {"app_connection_property": apc}
    app = get_app(rest_config)
    await aiohttp_client(app)  # instantiate here client so `on_startup` signal fires
    cfg = app[APP_CONFIG_KEY]
    assert cfg.app_connection_property == apc, "connection property wasn't applied in settings"
    assert await cfg.get_connection()
