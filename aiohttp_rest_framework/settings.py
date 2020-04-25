import typing

from aiohttp import web

from aiohttp_rest_framework.db import AioPGSAService, DatabaseServiceABC
from aiohttp_rest_framework.fields import AioPGSAInferredFieldBuilder

AIOPG_SA = "aiopg_sa"

SCHEMA_TYPES = (AIOPG_SA,)

db_orm_mappings = {
    AIOPG_SA: {
        "service": AioPGSAService,
        "field_builder": AioPGSAInferredFieldBuilder,
    }
}


class Config:
    def __init__(
            self,
            app: web.Application,
            *,
            app_connection_property: str = "db",
            get_connection: typing.Callable = None,
            db_service: typing.Type[DatabaseServiceABC] = None,
            schema_type: str = AIOPG_SA,
    ):
        assert isinstance(app_connection_property, str), (
            "`app_connection_property` has to be a string"
        )
        self.app_connection_property = app_connection_property

        assert schema_type in SCHEMA_TYPES, (
            f"`schema_type` has to be one of {', '.join(SCHEMA_TYPES)}"
        )

        def _get_connection():
            return app[app_connection_property]

        self.get_connection = get_connection or _get_connection
        assert callable(self.get_connection), "`get_connection` has to be callable"

        self.db_service_class = db_service or db_orm_mappings[schema_type]["service"]
        self.inferred_field_builder = db_orm_mappings[schema_type]["field_builder"]


APP_CONFIG_KEY = "rest_framework"

_config: typing.Optional[Config] = None


def get_global_config() -> Config:
    return _config


def setup_rest_framework(app: web.Application, settings: typing.Mapping = None) -> None:
    user_settings = settings or {}
    app_settings = Config(app, **user_settings)
    app[APP_CONFIG_KEY] = app_settings

    global _config
    _config = app_settings
