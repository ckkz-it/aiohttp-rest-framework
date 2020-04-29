import datetime
import enum

import marshmallow as ma
import pytest
from marshmallow import ValidationError

from aiohttp_rest_framework.fields import Enum, Interval


class MyEnum(enum.Enum):
    name_one = "Value_One"


def test_enum_field_by_value():
    my_enum_one = MyEnum.name_one
    field = Enum(MyEnum)
    serialized = field._serialize(my_enum_one)
    assert serialized == my_enum_one.value, "invalid serialization by value"

    deserialized = field._deserialize(serialized)
    assert deserialized == my_enum_one, "invalid deserialization by value"


def test_enum_field_by_name():
    my_enum_one = MyEnum.name_one
    field = Enum(MyEnum, by_value=False)
    serialized = field._serialize(my_enum_one)
    assert serialized == my_enum_one.name, "invalid serialization by name"

    deserialized = field._deserialize(serialized)
    assert deserialized == my_enum_one, "invalid deserialization by name"


def test_enum_serialize_null_value():
    field = Enum(MyEnum)
    assert field._serialize(None) is None


@pytest.mark.parametrize("non_string_value", [123, True, {}, []])
def test_enum_field_invalid_name_value(non_string_value):
    field = Enum(MyEnum, by_value=False)
    with pytest.raises(ma.exceptions.ValidationError, match="Not a valid string"):
        field._deserialize(non_string_value)


def test_enum_field_invalid_value():
    field = Enum(MyEnum)
    invalid_value = "not_from_enum"
    with pytest.raises(ma.exceptions.ValidationError, match="Not a valid value") as err:
        field._deserialize(invalid_value)
    for enm in MyEnum:
        assert err.match(enm.value), f"{enm.value} is not listed in valid enum values"

    field = Enum(MyEnum, by_value=False)
    with pytest.raises(ma.exceptions.ValidationError, match=r"Not a valid value") as err:
        field._deserialize(invalid_value)
    for enm in MyEnum:
        assert err.match(enm.name), f"{enm.name} is not listed in valid enum names"


@pytest.mark.parametrize("interval, expected_timedelta", [
    ("3 hours 2 minutes 3 seconds", datetime.timedelta(hours=3, minutes=2, seconds=3)),
    ("3 hours 3 seconds", datetime.timedelta(hours=3, seconds=3)),
    (86400, datetime.timedelta(seconds=86400)),
])
# no need to test serialization, because serialization is inherited from ma's `TimeDelta` field
async def test_interval_field_deserialization(interval, expected_timedelta):
    value = Interval().deserialize(interval)
    assert isinstance(value, datetime.timedelta), "Interval deserialized not in timedelta"
    assert value == expected_timedelta, "invalid Interval deserialization value"


async def test_interval_overflow_error():
    with pytest.raises(ValidationError):
        max_seconds = (datetime.timedelta.max.days + 1) * 24 * 60 * 60
        Interval().deserialize(max_seconds)


def test_interval_invalid_range_err():
    with pytest.raises(ValidationError):
        Interval().deserialize("invalid range")


def test_interval_zero_range_not_allowed():
    with pytest.raises(ValidationError):
        Interval(allow_zero=False).deserialize(0)


def test_interval_zero_range_allowed():
    interval: datetime.timedelta = Interval(allow_zero=True).deserialize(0)
    assert interval.total_seconds() == 0
