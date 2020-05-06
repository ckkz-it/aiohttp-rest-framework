import abc
import datetime
import inspect
import re
import typing
from functools import partial

import marshmallow as ma
import sqlalchemy as sa
from marshmallow.fields import *  # noqa
from marshmallow.fields import __all__ as ma_fields_all  # noqa
from psycopg2.extensions import PYINTERVAL
from sqlalchemy.dialects.postgresql import ARRAY, JSON
from sqlalchemy.dialects.postgresql import UUID as PgUUID

from aiohttp_rest_framework.types import SASerializerFieldMapping
from aiohttp_rest_framework.utils import ClassLookupDict, safe_issubclass

__all__ = ["Enum", "UUID", "Interval", "patch_ma_fields"] + ma_fields_all

# A flag to mark that marshamallow's fields were patched by aiohttp-rest-framework
# i.e. `read_only` and `write_only` were mapped to `dump_only` and `load_only`,
# `required` set to True by default (initially it's False, by should be True like in drf)
_MA_FIELDS_PATCHED = False


def patch_ma_fields():
    """
    Make all marshmallow's fields required by default
    """
    global _MA_FIELDS_PATCHED
    if _MA_FIELDS_PATCHED:
        return
    globals_ = globals()
    items_to_update = {}
    for key, value in globals_.items():
        if safe_issubclass(value, ma.fields.FieldABC):
            class patched(value):
                _rf_patched = True

                def __init__(self, *args, **kwargs):
                    kwargs.setdefault("required", True)
                    kwargs.setdefault("dump_only", kwargs.pop("read_only", False))
                    kwargs.setdefault("load_only", kwargs.pop("write_only", False))
                    super(self.__class__, self).__init__(*args, **kwargs)

            mro = inspect.getmro(patched)[1:]  # remove `patched` class from mro
            patched = type(key, mro, dict(vars(patched)))
            items_to_update[key] = patched

    globals_.update(**items_to_update)

    # also update mapping with patched classes
    for key, value in sa_ma_pg_field_mapping.items():
        if value.__name__ in items_to_update:
            sa_ma_pg_field_mapping[key] = items_to_update[value.__name__]  # noqa

    _MA_FIELDS_PATCHED = True


# @todo: add support for multiple enums
class Enum(ma.fields.Field):
    default_error_messages = {
        "invalid_string": "Not a valid string.",
        "invalid_enum": "Not a valid value, has to be one of ({values}).",
    }

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
        self.as_uuid = kwargs.pop("as_uuid", False)  # support sqlalchemy's postgres uuid `as_uuid`
        super().__init__(**kwargs)

    def _deserialize(self, value, attr, data, **kwargs):
        # Keep validation from marshmallow, but stringify field if `as_uuid=False`
        uuid = super()._deserialize(value, attr, data, **kwargs)
        if self.as_uuid:
            return uuid
        return str(uuid)


# @todo: add support for weeks
class Interval(ma.fields.TimeDelta):
    default_error_messages = {
        "invalid": "Not a valid period of time.",
        "format": "{input!r} cannot be formatted as a timedelta.",
        "zero": "Zero interval is not allowed",
    }

    INTERVAL_RE = re.compile(r".*\d+\s*\w+.*")  # digit + letter(s)
    HOURS_RE = re.compile(r".*(?P<full_match>(?P<amount>\d+)\s*hours?\s*)")
    MINUTES_RE = re.compile(r".*(?P<full_match>(?P<amount>\d+)\s*minutes?\s*)")
    SECONDS_RE = re.compile(r".*(?P<full_match>(?P<amount>\d+)\s*seconds?\s*)")

    def __init__(self, *args, **kwargs):
        self.allow_zero = kwargs.pop("allow_zero", False)
        super().__init__(*args, **kwargs)

    def _deserialize(self, value, attr, data, **kwargs) -> datetime.timedelta:
        try:
            value = int(value)
        except (TypeError, ValueError):
            # try to adapt postgres intervals (e.g. "3 month", "1 year -4 days") with psycopg2
            try:
                if not self.INTERVAL_RE.match(value):
                    raise ValueError
                # psycopg adapter can not parse `hours`, `minutes`, and `seconds` keywords,
                # we need to replace them to `3:22:1` format first
                value = self._prepare_value_for_pg(value)
                return PYINTERVAL(value, None)  # 2nd argument is unknown
            except (TypeError, ValueError, IndexError) as error:
                raise self.make_error("invalid") from error

        try:
            interval: datetime.timedelta = datetime.timedelta(**{self.precision: value})
            if interval.total_seconds() == 0 and not self.allow_zero:
                raise self.make_error("zero")
            return interval
        except OverflowError as error:
            raise self.make_error("invalid") from error

    def _prepare_value_for_pg(self, value: str):
        """ Replace 1 hour 2 minutes 3 seconds to 1:2:3 form"""
        hours = False
        minutes = False
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


class FieldBuilderABC(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def build(self, *args, **kwargs) -> ma.fields.Field:
        """
        Implement building marshmallow field based on database field
        :return: field
        """
        pass


class AioPGSAFieldBuilder(FieldBuilderABC):
    def build(
            self,
            name: str,
            serializer=None,
            **kwargs
    ):
        model: sa.Table = serializer.opts.model
        column: sa.Column = model.columns.get(name)
        assert column is not None, (
            f"{name} was not found for {serializer.__class__.__name__} serializer "
            f"in {model.name} model"
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
            kwargs.setdefault("dump_only", True)  # pk is read only
            kwargs.setdefault("required", False)
        # can't set `missing` when `required` is true, so check it first
        # also do not set default for pk, default value will be populated on db (or sa) level
        if column.default and not column.primary_key and not kwargs.get("required", False):
            kwargs["required"] = False
            default = column.default.arg
            if column.default.is_callable:
                # sqlalchemy wraps callable into lambdas which accepts dialect context,
                # strip this context argument to make `default` simple callable (with no arguments)
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
