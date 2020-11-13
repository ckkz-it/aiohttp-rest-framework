import typing

import marshmallow as ma
from sqlalchemy.sql.type_api import TypeEngine

__all__ = (
    "Fetch",
    "SASerializerFieldMapping",
    "DbOrmMappingEntity",
    "DbOrmMapping",
)

Fetch = typing.Literal["one", "all"]

SASerializerFieldMapping = typing.Dict[typing.Type[TypeEngine], typing.Type[ma.fields.Field]]

DbOrmMappingEntity = typing.Mapping[str, typing.Any]
DbOrmMapping = typing.Mapping[str, DbOrmMappingEntity]
