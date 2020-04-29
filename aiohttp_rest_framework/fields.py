import abc
import datetime
import re
import typing
from functools import partial

import marshmallow as ma
import sqlalchemy as sa
from psycopg2.extensions import PYINTERVAL
from sqlalchemy.dialects.postgresql import ARRAY, JSON
from sqlalchemy.dialects.postgresql import UUID as PgUUID
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


# @todo: add field tests
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


# @todo: add field tests
class Interval(ma.fields.TimeDelta):
    HOURS_RE = re.compile(r".*(?P<full_match>(?P<amount>\d+)\s*hours?\s*)")
    MINUTES_RE = re.compile(r".*(?P<full_match>(?P<amount>\d+)\s*minutes?\s*)")
    SECONDS_RE = re.compile(r".*(?P<full_match>(?P<amount>\d+)\s*seconds?\s*)")

    def _deserialize(self, value, attr, data, **kwargs) -> datetime.timedelta:
        try:
            value = int(value)
        except (TypeError, ValueError):
            # try to adapt postgres intervals (e.g. "3 month", "1 year -4 days") with psycopg2
            try:
                # psycopg adapter can not parse `hours`, `minutes`, and `seconds` keywords,
                # we need to replace them to `3:22:1` form first
                value = self._prepare_value_for_pg(value)
                return PYINTERVAL(value, None)  # 2nd argument is unknown
            except (TypeError, ValueError, IndexError) as error:
                raise self.make_error("invalid") from error

        try:
            return datetime.timedelta(**{self.precision: value})
        except OverflowError as error:
            raise self.make_error("invalid") from error

    def _prepare_value_for_pg(self, value: str):
        """ Replace 1 hour 2 minutes 3 seconds to 1:2:3 form"""
        hours = False
        minutes = False
        # @todo: use walrus here when pycodestyle will be updated to 2.6.0, now it breaks flake8
        if self.HOURS_RE.match(value):
            match = self.HOURS_RE.match(value)
            # leave trailing colon if only hours will be presented in str
            # `5:` is considered as 5 hours 0 minutes
            value = value.replace(match.group("full_match"), f"{match.group('amount')}:")
            hours = True
        if self.MINUTES_RE.match(value):
            match = self.MINUTES_RE.match(value)
            prefix = "" if hours else "0:"
            value = value.replace(match.group("full_match"), f"{prefix}{match.group('amount')}")
            minutes = True
        if self.SECONDS_RE.match(value):
            match = self.SECONDS_RE.match(value)
            prefix = "0:0:"
            if hours:
                if minutes:
                    prefix = ":"
                else:
                    prefix = "0:"
            value = value.replace(match.group("full_match"), f"{prefix}{match.group('amount')}")
        return value.strip()


SASerializerFieldMapping = typing.Dict[typing.Type[TypeEngine], typing.Type[ma.fields.Field]]

sa_ma_field_mapping: SASerializerFieldMapping = {
    sa.BigInteger: ma.fields.Integer,
    sa.Boolean: ma.fields.Boolean,
    sa.Date: ma.fields.Date,
    sa.DateTime: ma.fields.DateTime,
    sa.Enum: Enum,
    sa.Float: ma.fields.Float,
    sa.Integer: ma.fields.Integer,
    sa.Interval: Interval,
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
            f"in {model.name} model"
        )

        mapping = ClassLookupDict(sa_ma_pg_field_mapping)
        field_cls = mapping.get(column.type, ma.fields.Inferred)

        self._set_db_specific_kwargs(kwargs, column)
        self._set_field_specific_kwargs(kwargs, field_cls, column)
        kwargs.setdefault("required", True)  # by default all fields are required
        field = field_cls(**kwargs)
        return field

    def _set_db_specific_kwargs(self, kwargs: dict, column: sa.Column):
        if column.nullable:
            kwargs.setdefault("allow_none", True)
        if column.primary_key:
            kwargs.setdefault("dump_only", True)  # pk is read only
            kwargs.setdefault("required", False)
        # can't set `missing` when `required` is true
        if column.default and not column.primary_key and not kwargs.get("required", False):
            kwargs["required"] = False
            default = column.default.arg
            if callable(default):
                # sqlalchemy wraps callable into lambdas which accepts context,
                # strip this context argument to make default simple callable (with no arguments)
                default = partial(default, {})
            kwargs.setdefault("missing", default)  # ma's `missing` is like drf's `default`
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
            kwargs["enum"] = enum.__class__

        if field_cls is UUID:
            kwargs["as_uuid"] = column.type.as_uuid
