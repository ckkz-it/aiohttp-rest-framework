import abc
import typing

import marshmallow as ma
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, JSON, UUID

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


sa_ma_field_mapping = {
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

sa_ma_pg_field_mapping = {
    **sa_ma_field_mapping,
    UUID: ma.fields.UUID,
    ARRAY: ma.fields.List,
    JSON: ma.fields.Dict,
}


class InferredABC(ma.fields.Field, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def _build_field(self, *args, **kwargs) -> ma.fields.Field:
        """
        Implement getting marshmallow field based on database field
        :return: field
        """
        pass


class AioPGSAInferred(InferredABC):
    def __init__(self, **kwargs):
        super().__init__()
        # `self.model` attribute is for standalone use, primarily for tests,
        # most likely you won't use it your application
        # when used with serializer, `self.root` is not defined here yet
        # so leave it until `self._build_field()` is called to define model
        self.model: sa.Table = kwargs.pop("model", None)
        self.kwargs = kwargs
        self._field: typing.Optional[typing.Type[ma.fields.Field]] = None

    def _serialize(self, value, attr: typing.Optional[str], obj, **kwargs):
        if self._field is None:
            self._field = self._build_field(value)
        return self._field._serialize(value, attr, obj, **kwargs)

    def _deserialize(self, value, attr: typing.Optional[str], data, **kwargs):
        if self._field is None:
            self._field = self._build_field(value)
        return self._field._deserialize(value, attr, data, **kwargs)

    def _build_field(self, value):
        assert self.parent is not None or self.model is not None, (
            "When use field in standalone mode (without binding to serializer) "
            "you have to pass `model` kwarg on field initialization"
        )
        model: sa.Table
        if self.model is not None:
            model = self.model
        else:
            model = self.root.opts.model
        column = model.columns.get(self.name)
        assert column is not None, (
            f"{self.name} was not found for {self.root.__class__.__name__} serializer "
            f"in {model.__name__} model"
        )

        mapping = ClassLookupDict(sa_ma_pg_field_mapping)
        field_cls = mapping.get(column.type)
        if field_cls is None and self.root:
            field_cls = self.root.TYPE_MAPPING.get(type(value))
        if field_cls is None:
            field_cls = ma.fields.Field

        self._set_db_specific_kwargs(column)
        if field_cls is Enum:
            enum_name = column.type.enums[0]
            enum = column.type.enum_class[enum_name]
            field = typing.cast(typing.Type[Enum], field_cls)(enum, **self.kwargs)
        else:
            field = field_cls(**self.kwargs)
        field._bind_to_schema(self.name, self.parent)
        return field

    def _set_db_specific_kwargs(self, column: sa.Column):
        if column.nullable:
            self.kwargs.setdefault("allow_none", True)
        if column.primary_key:
            self.kwargs.setdefault("dump_only", True)
            self.kwargs.setdefault("allow_none", False)
        if column.default:
            self.kwargs.setdefault("required", False)
            self.kwargs.setdefault("missing", column.default.arg)
        if column.server_default:
            self.kwargs.setdefault("required", False)
