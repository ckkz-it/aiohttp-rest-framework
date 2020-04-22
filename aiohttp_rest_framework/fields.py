import enum

import sqlalchemy as sa
import marshmallow as ma
import typing


class Enum(ma.fields.String):
    default_error_messages = {
        "invalid_string": "Not a valid string.",
        "invalid_enum": "Not a valid value, has to be one of ({values}).",
    }
    by_value: bool = True

    def __init__(self, enum_class: typing.Type[enum.Enum], by_value=True, **kwargs):
        self.enum = enum_class
        self.by_value = by_value
        super().__init__(**kwargs)

    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return None
        if self.by_value:
            return value.value
        return value.name

    def _deserialize(self, value, attr, data, **kwargs):
        if self.by_value:
            try:
                return self.enum(value)
            except ValueError:
                raise self.make_error("invalid_enum", values=", ".join(x.value for x in self.enum))

        if not isinstance(value, str):
            raise self.make_error("invalid_string")
        if hasattr(self.enum, value):
            raise self.make_error("invalid_enum", values=", ".join(x.name for x in self.enum))
        return getattr(self.enum, value)


sqlalchemy_serializer_field_mapping = {
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
    sa.ARRAY: ma.fields.List,
    sa.JSON: ma.fields.Dict,
}
