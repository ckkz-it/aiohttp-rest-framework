import enum

import marshmallow as ma
import pytest

from aiohttp_rest_framework.fields import Enum


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


def test_enum_field_invalid_name_value():
    field = Enum(MyEnum, by_value=False)
    not_string_value1 = 123
    not_string_value2 = True
    with pytest.raises(ma.exceptions.ValidationError, match="Not a valid string"):
        field._deserialize(not_string_value1)
    with pytest.raises(ma.exceptions.ValidationError, match="Not a valid string"):
        field._deserialize(not_string_value2)


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
