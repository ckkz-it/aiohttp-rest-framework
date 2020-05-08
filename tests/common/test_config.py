import asyncio

import pytest

from aiohttp_rest_framework import APP_CONFIG_KEY
from aiohttp_rest_framework.settings import AIOPG_SA, DEFAULT_APP_CONN_PROP
from tests.base_app import get_base_app


def test_default_config_setup():
    app = get_base_app()
    assert APP_CONFIG_KEY in app, "rest config isn't presented in app"
    cfg = app[APP_CONFIG_KEY]
    assert hasattr(cfg, "get_connection"), "config doesn't have `get_connection` attribute"
    assert hasattr(cfg, "db_service_class"), "config doesn't have `db_service_class` attribute"
    assert hasattr(cfg, "_db_orm_mapping")
    assert cfg.app_connection_property == DEFAULT_APP_CONN_PROP
    assert cfg._schema_type == AIOPG_SA


@pytest.mark.parametrize("get_connection", ("wrong_get_conn", lambda: "some connection"))
def test_wrong_get_connection_config_setup(get_connection):
    rest_config = {"get_connection": get_connection}
    with pytest.raises(AssertionError, match="`get_connection` has to be async callable"):
        get_base_app(rest_config)


async def test_config_setup_with_async_get_connection():
    async def get_conn():
        return "some connection"

    rest_config = {"get_connection": get_conn}
    app = get_base_app(rest_config)
    cfg = app[APP_CONFIG_KEY]
    assert cfg.get_connection is get_conn, "wrong custom `get_connection` applied to settings"
    assert asyncio.iscoroutinefunction(cfg.get_connection), "`get_connection` is not async"
    assert await cfg.get_connection() == await get_conn()


@pytest.mark.parametrize("conn_prop", ["valid", "123valid", "va_lid", "va123lid", "va_li_d"])
def test_config_valid_app_connection_property(conn_prop):
    rest_config = {"app_connection_property": conn_prop}
    app = get_base_app(rest_config)
    cfg = app[APP_CONFIG_KEY]
    assert cfg.app_connection_property == conn_prop


@pytest.mark.parametrize("conn_prop", [123, "with-hyphen", "with space"])
def test_config_invalid_app_connection_property(conn_prop):
    rest_config = {"app_connection_property": conn_prop}
    with pytest.raises(AssertionError, match="app_connection_property"):
        get_base_app(rest_config)


def test_invalid_schema_type():
    rest_config = {"schema_type": "invalid"}
    with pytest.raises(AssertionError, match="`schema_type` has to be one of"):
        get_base_app(rest_config)
