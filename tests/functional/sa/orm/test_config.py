from aiohttp.test_utils import unittest_run_loop

from aiohttp_rest_framework import APP_CONFIG_KEY
from tests.functional.sa.orm.base import BaseTestCase


class ConfigTestCase(BaseTestCase):
    def setUp(self) -> None:
        self.apc = "engine"
        self.rest_config = {"app_connection_property": self.apc}
        super().setUp()

    @unittest_run_loop
    async def test_config_app_connection_property(self) -> None:
        cfg = self.app[APP_CONFIG_KEY]
        self.assertEqual(cfg.app_connection_property, self.apc)
        self.assertIsNotNone(await cfg.get_connection())
