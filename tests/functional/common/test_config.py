import asyncio
from unittest import IsolatedAsyncioTestCase

from aiohttp_rest_framework import APP_CONFIG_KEY
from aiohttp_rest_framework.settings import DEFAULT_APP_CONN_PROP, SA
from tests.test_app.base_app import get_base_app


class ConfigTestCase(IsolatedAsyncioTestCase):
    def test_default_config_setup(self) -> None:
        app = get_base_app()
        assert APP_CONFIG_KEY in app, "rest config isn't presented in app"
        cfg = app[APP_CONFIG_KEY]
        self.assertTrue(hasattr(cfg, "get_connection"))
        self.assertTrue(hasattr(cfg, "db_manager_class"))
        self.assertTrue(hasattr(cfg, "_db_orm_mapping"))
        self.assertEqual(cfg.app_connection_property, DEFAULT_APP_CONN_PROP)
        self.assertTrue(cfg.schema_type, SA)

    def test_wrong_get_connection_config_setup(self) -> None:
        for get_connection in ["wrong_get_conn", lambda: "some connection"]:
            rest_config = {"get_connection": get_connection}
            with self.assertRaises(AssertionError) as exc_info:
                get_base_app(rest_config)
            self.assertIn("`get_connection` has to be async callable", exc_info.exception.args[0])

    async def test_config_setup_with_async_get_connection(self) -> None:
        async def get_conn():
            return "some connection"

        rest_config = {"get_connection": get_conn}
        app = get_base_app(rest_config)
        cfg = app[APP_CONFIG_KEY]
        self.assertIs(cfg.get_connection, get_conn)
        self.assertTrue(asyncio.iscoroutinefunction(cfg.get_connection))
        self.assertTrue(await cfg.get_connection(), await get_conn())

    def test_config_valid_app_connection_property(self) -> None:
        for conn_prop in ["valid", "123valid", "va_lid", "va123lid", "va_li_d"]:
            rest_config = {"app_connection_property": conn_prop}
            app = get_base_app(rest_config)
            cfg = app[APP_CONFIG_KEY]
            self.assertEqual(cfg.app_connection_property, conn_prop)

    def test_config_invalid_app_connection_property(self) -> None:
        for conn_prop in [123, "with-hyphen", "with space"]:
            rest_config = {"app_connection_property": conn_prop}
            with self.assertRaises(AssertionError) as exc_info:
                get_base_app(rest_config)
            self.assertIn("app_connection_property", exc_info.exception.args[0])

    def test_invalid_schema_type(self) -> None:
        rest_config = {"schema_type": "invalid"}
        with self.assertRaises(AssertionError) as exc_info:
            get_base_app(rest_config)
        self.assertIn("`schema_type` has to be one of", exc_info.exception.args[0])
