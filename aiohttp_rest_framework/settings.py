import asyncio
import re
from typing import Awaitable, Callable, Optional

from aiohttp import web

from aiohttp_rest_framework.db.base import BaseDBManager
from aiohttp_rest_framework.db.sa import SAManager
from aiohttp_rest_framework.fields import SAFieldBuilder
from aiohttp_rest_framework.types import DbOrmMapping
from aiohttp_rest_framework.utils import get_model_fields_sa

__all__ = (
    "SA",
    "Config",
    "get_global_config",
    "set_global_config",
    "DEFAULT_APP_CONN_PROP",
)

SA = "sa"
SCHEMA_TYPES = (SA,)

db_orm_mappings: DbOrmMapping = {
    SA: {
        "manager": SAManager,
        "field_builder": SAFieldBuilder,
        "model_fields_getter": get_model_fields_sa,
    },
}

DEFAULT_APP_CONN_PROP = "db"
CONNECTION_PROP_RE = re.compile(r"^[^-\s]+$")


class Config:
    def __init__(
        self,
        app: web.Application,
        *,
        app_connection_property: str = DEFAULT_APP_CONN_PROP,
        get_connection: Optional[Callable[[], Awaitable]] = None,
        db_manager: Optional[BaseDBManager] = None,
        schema_type: str = SA,
    ):
        assert isinstance(app_connection_property, str), (
            "`app_connection_property` has to be a string"
        )
        assert CONNECTION_PROP_RE.match(app_connection_property), (
            "`app_connection_property` must not have spaces and hyphens"
        )
        self.app = app
        self.app_connection_property = app_connection_property

        assert schema_type in SCHEMA_TYPES, (
            f"`schema_type` has to be one of {', '.join(SCHEMA_TYPES)}"
        )
        self.schema_type = schema_type
        self._db_orm_mapping = db_orm_mappings[schema_type]

        async def _get_connection():
            return app[app_connection_property]

        self.get_connection = get_connection or _get_connection
        assert callable(self.get_connection) and asyncio.iscoroutinefunction(self.get_connection), (
            "`get_connection` has to be async callable"
        )

        self.db_manager_class = db_manager or self._db_orm_mapping["manager"]
        self.field_builder = self._db_orm_mapping["field_builder"]
        self.get_model_fields = self._db_orm_mapping["model_fields_getter"]


_config: Optional[Config] = None


def get_global_config() -> Config:
    err_msg = "Looks like you didn't call `setup_rest_framework(app)`"
    assert _config, err_msg
    return _config


def set_global_config(config: Config) -> None:
    global _config
    _config = config
