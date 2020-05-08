import typing

import marshmallow as ma
from aiopg.sa.result import ResultProxy, RowProxy
from sqlalchemy.sql.type_api import TypeEngine

__all__ = (
    "ExecuteResultAioPgSA",
    "Fetch",
    "SASerializerFieldMapping",
    "DbOrmMappingEntity",
    "DbOrmMapping",
)

ExecuteResultAioPgSA = typing.Union[typing.List[RowProxy], typing.Optional[RowProxy], ResultProxy]

Fetch = typing.Literal["one", "all"]

SASerializerFieldMapping = typing.Dict[typing.Type[TypeEngine], typing.Type[ma.fields.Field]]

DbOrmMappingEntity = typing.Mapping[str, typing.Any]
DbOrmMapping = typing.Mapping[str, DbOrmMappingEntity]
