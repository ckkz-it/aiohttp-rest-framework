import pytest

from aiohttp_rest_framework.settings import APP_CONFIG_KEY
from tests.base_app import get_base_app


def test_default_config_setup():
    app = get_base_app()
    assert APP_CONFIG_KEY in app, "rest config isn't presented in app"
    cfg = app[APP_CONFIG_KEY]

    assert hasattr(cfg, "get_connection"), "config doesn't have `get_connection` attribute"
    assert callable(cfg.get_connection), "`get_connection` isn't callable"

    assert hasattr(cfg, "db_service_class"), (
        "config doesn't have `db_service_class` attribute"
    )


def test_wrong_get_connection_config_setup():
    rest_config = {
        "get_connection": "not callable",
    }
    with pytest.raises(AssertionError, match="`get_connection` has to be callable"):
        get_base_app(rest_config)


def test_config_setup_with_custom_connection():
    conn = "some connection"
    rest_config = {
        "connection": conn,
    }
    app = get_base_app(rest_config)
    cfg = app[APP_CONFIG_KEY]
    assert cfg.get_connection() == conn, "custom connection wasn't applied"


def test_config_setup_with_custom_get_connection():
    get_conn = lambda: "some connection"
    rest_config = {
        "get_connection": get_conn,
    }
    app = get_base_app(rest_config)
    cfg = app[APP_CONFIG_KEY]
    assert cfg.get_connection is get_conn, "wrong custom `get_connection` applied to settings"
    assert cfg.get_connection() == get_conn()


def test_get_connection_and_connection_provided_to_config():
    rest_config = {
        "get_connection": lambda: "some connection",
        "connection": "some connection",
    }
    with pytest.raises(AssertionError, match="either provide"):
        get_base_app(rest_config)
