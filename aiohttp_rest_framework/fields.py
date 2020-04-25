import abc
import typing
from functools import partial

import marshmallow as ma
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, JSON, UUID as PgUUID
from sqlalchemy.sql.type_api import TypeEngine

from aiohttp_rest_framework.utils import ClassLookupDict


class Enum(ma.fields.Field):
    default_error_messages = {
        "invalid_string": "Not a valid string.",
        "invalid_enum": "Not a valid value, has to be one of ({values}).",
    }
    by_value: bool = True

    def __init__(self, enum, by_value=True, **kwargs):
        self.enum = enum
        self.by_value = by_value
        super().__init__(**kwargs)

    def _serialize(self, value, *args, **kwargs):
        if value is None:
            return None
        if self.by_value:
            return value.value
        return value.name

    def _deserialize(self, value, *args, **kwargs):
        if self.by_value:
            try:
                return self.enum(value)
            except ValueError:
                raise self.make_error("invalid_enum", values=", ".join(x.value for x in self.enum))

        if not isinstance(value, str):
            raise self.make_error("invalid_string")
        if not hasattr(self.enum, value):
            raise self.make_error("invalid_enum", values=", ".join(x.name for x in self.enum))
        return getattr(self.enum, value)


class UUID(ma.fields.UUID):
    def __init__(self, **kwargs):
        self.as_uuid = kwargs.pop("as_uuid", True)  # support sqlalchemy's postgres uuid `as_uuid`
        super().__init__(**kwargs)

    def _deserialize(self, value, attr, data, **kwargs):
        # Keep validation from marshmallow, but stringify field if `as_uuid=False`
        uuid = super()._deserialize(value, attr, data, **kwargs)
        if self.as_uuid:
            return uuid
        return str(uuid)


SASerializerFieldMapping = typing.Dict[typing.Type[TypeEngine], typing.Type[ma.fields.Field]]

sa_ma_field_mapping: SASerializerFieldMapping = {
    sa.BigInteger: ma.fields.Integer,
    sa.Boolean: ma.fields.Boolean,
    sa.Date: ma.fields.Date,
    sa.DateTime: ma.fields.DateTime,
    sa.Enum: Enum,
    sa.Float: ma.fields.Float,
    sa.Integer: ma.fields.Integer,
    sa.Interval: ma.fields.TimeDelta,
    sa.Numeric: ma.fields.Decimal,
    sa.SmallInteger: ma.fields.Integer,
    sa.String: ma.fields.String,
    sa.Text: ma.fields.String,
    sa.Time: ma.fields.Time,
    sa.Unicode: ma.fields.String,
    sa.UnicodeText: ma.fields.String,
}

sa_ma_pg_field_mapping: SASerializerFieldMapping = {
    **sa_ma_field_mapping,
    PgUUID: UUID,
    ARRAY: ma.fields.List,
    JSON: ma.fields.Dict,
}


class InferredFieldBuilderABC(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def build(self, *args, **kwargs) -> ma.fields.Field:
        """
        Implement building marshmallow field based on database field
        :return: field
        """
        pass


class AioPGSAInferredFieldBuilder(InferredFieldBuilderABC):
    def __init__(self, name: str, serializer=None, model: sa.Table = None):
        self.name = name
        self.serializer = serializer
        self.model = model

    def build(self, **kwargs):
        assert self.serializer is not None or self.model is not None, (
            "When use field in standalone mode (without binding to serializer) "
            "you have to pass `model` kwarg on field initialization"
        )
        model = self.model if self.model is not None else self.serializer.opts.model
        column = model.columns.get(self.name)
        assert column is not None, (
            f"{self.name} was not found for {self.serializer.__class__.__name__} serializer "
            f"in {model.__name__} model"
        )

        mapping = ClassLookupDict(sa_ma_pg_field_mapping)
        field_cls = mapping.get(column.type, ma.fields.Inferred)

        self._set_db_specific_kwargs(kwargs, column)
        self._set_field_specific_kwargs(kwargs, field_cls, column)
        field = field_cls(**kwargs)
        return field

    def _set_db_specific_kwargs(self, kwargs: dict, column: sa.Column):
        if column.nullable:
            kwargs.setdefault("allow_none", True)
        if column.primary_key:
            kwargs.setdefault("dump_only", True)
            kwargs.setdefault("required", False)
        if column.default and not column.primary_key:
            kwargs.setdefault("required", False)
            default = column.default.arg
            if callable(default):
                # sqlalchemy wraps callable into lambdas which accepts context
                # strip this context argument
                default = partial(default, {})
            kwargs.setdefault("missing", default)
        if column.server_default:
            kwargs.setdefault("required", False)

    def _set_field_specific_kwargs(self, kwargs: dict, field_cls: typing.Type[ma.fields.Field],
                                   column: sa.Column):
        if field_cls is Enum:  # for `Enum` we have to point which enum class is being used
            if len(column.type.enums) > 1:
                # @todo: implement support
                msg = (
                    "aiohttp-rest-framework does not support postgres `Enum` field "
                    "with multiple enum classes"
                )
                raise ValueError(msg)
            enum_name = column.type.enums[0]
            enum = column.type.enum_class[enum_name]
            kwargs["enum"] = enum

        if field_cls is UUID:
            kwargs["as_uuid"] = column.type.as_uuid
