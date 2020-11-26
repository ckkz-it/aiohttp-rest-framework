import typing

import marshmallow as ma
from sqlalchemy.sql.type_api import TypeEngine

__all__ = (
    "SASerializerFieldMapping",
    "DbOrmMappingEntity",
    "DbOrmMapping",
)

SASerializerFieldMapping = typing.Dict[typing.Type[TypeEngine], typing.Type[ma.fields.Field]]

DbOrmMappingEntity = typing.Mapping[str, typing.Any]
DbOrmMapping = typing.Mapping[str, DbOrmMappingEntity]
