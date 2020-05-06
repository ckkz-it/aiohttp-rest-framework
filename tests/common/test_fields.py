import datetime
import enum

import marshmallow as ma
import pytest

from aiohttp_rest_framework import fields


class MyEnum(enum.Enum):
    name_one = "Value_One"


def test_enum_field_by_value():
    my_enum_one = MyEnum.name_one
    field = fields.Enum(MyEnum)
    serialized = field._serialize(my_enum_one)
    assert serialized == my_enum_one.value, "invalid serialization by value"

    deserialized = field._deserialize(serialized)
    assert deserialized == my_enum_one, "invalid deserialization by value"


def test_enum_field_by_name():
    my_enum_one = MyEnum.name_one
    field = fields.Enum(MyEnum, by_value=False)
    serialized = field._serialize(my_enum_one)
    assert serialized == my_enum_one.name, "invalid serialization by name"

    deserialized = field._deserialize(serialized)
    assert deserialized == my_enum_one, "invalid deserialization by name"


def test_enum_serialize_null_value():
    field = fields.Enum(MyEnum)
    assert field._serialize(None) is None


@pytest.mark.parametrize("non_string_value", [123, True, {}, []])
def test_enum_field_invalid_name_value(non_string_value):
    field = fields.Enum(MyEnum, by_value=False)
    with pytest.raises(ma.ValidationError, match="Not a valid string"):
        field._deserialize(non_string_value)


def test_enum_field_invalid_value():
    field = fields.Enum(MyEnum)
    invalid_value = "not_from_enum"
    with pytest.raises(ma.ValidationError, match="Not a valid value") as err:
        field._deserialize(invalid_value)
    for enm in MyEnum:
        assert err.match(enm.value), f"{enm.value} is not listed in valid enum values"

    field = fields.Enum(MyEnum, by_value=False)
    with pytest.raises(ma.ValidationError, match=r"Not a valid value") as err:
        field._deserialize(invalid_value)
    for enm in MyEnum:
        assert err.match(enm.name), f"{enm.name} is not listed in valid enum names"


@pytest.mark.parametrize("interval, expected_timedelta", [
    ("3 hours 2 minutes 3 seconds", datetime.timedelta(hours=3, minutes=2, seconds=3)),
    ("3 hours 3 seconds", datetime.timedelta(hours=3, seconds=3)),
    (86400, datetime.timedelta(seconds=86400)),
])
async def test_interval_field_deserialization(interval, expected_timedelta):
    # no need to test serialization, because serialization is inherited from ma's `TimeDelta` field
    value = fields.Interval().deserialize(interval)
    assert isinstance(value, datetime.timedelta), "Interval deserialized not in timedelta"
    assert value == expected_timedelta, "invalid Interval deserialization value"


async def test_interval_overflow_error():
    with pytest.raises(ma.ValidationError):
        max_seconds = (datetime.timedelta.max.days + 1) * 24 * 60 * 60
        fields.Interval().deserialize(max_seconds)


def test_interval_invalid_range_err():
    with pytest.raises(ma.ValidationError):
        fields.Interval().deserialize("invalid range")


def test_interval_zero_range_not_allowed():
    with pytest.raises(ma.ValidationError):
        fields.Interval().deserialize(0)


def test_interval_zero_range_allowed():
    interval: datetime.timedelta = fields.Interval(allow_zero=True).deserialize(0)
    assert interval.total_seconds() == 0


def test_ma_fields_patched():
    for key, value in vars(fields).items():
        try:
            if issubclass(value, ma.fields.Field):
                assert value._rf_patched  # noqa
                assert value().required, (
                    f"`required` default True was not patched for {value.__name__} field"
                )
        except TypeError:
            pass
