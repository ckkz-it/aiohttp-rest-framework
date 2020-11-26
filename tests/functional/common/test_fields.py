import datetime
import enum
from unittest import TestCase

import marshmallow as ma

from aiohttp_rest_framework import fields
from aiohttp_rest_framework.serializers import Serializer
from aiohttp_rest_framework.utils import safe_issubclass


class MyEnum(enum.Enum):
    name_one = "Value_One"
    name_two = "Value_Two"


class FieldsTestCase(TestCase):
    def test_enum_field_by_value(self) -> None:
        my_enum_one = MyEnum.name_one
        field = fields.Enum(MyEnum)
        serialized = field._serialize(my_enum_one)
        self.assertEqual(serialized, my_enum_one.value, "invalid serialization by value")

        deserialized = field._deserialize(serialized)
        self.assertEqual(deserialized, my_enum_one, "invalid deserialization by value")

    def test_enum_field_by_name(self) -> None:
        my_enum_one = MyEnum.name_one
        field = fields.Enum(MyEnum, by_value=False)
        serialized = field._serialize(my_enum_one)
        self.assertEqual(serialized, my_enum_one.name, "invalid serialization by name")

        deserialized = field._deserialize(serialized)
        self.assertEqual(deserialized, my_enum_one, "invalid deserialization by name")

    def test_enum_serialize_null_value(self) -> None:
        field = fields.Enum(MyEnum)
        assert field._serialize(None) is None

    def test_enum_field_invalid_name_value(self) -> None:
        for non_string_value in [123, True, {}, []]:
            field = fields.Enum(MyEnum, by_value=False)
            with self.assertRaises(ma.ValidationError) as exc_info:
                field._deserialize(non_string_value)
            self.assertIn("Not a valid string", exc_info.exception.args[0])

    def test_enum_field_invalid_value(self) -> None:
        field = fields.Enum(MyEnum)
        invalid_value = "not_from_enum"
        with self.assertRaises(ma.ValidationError) as exc_info:
            field._deserialize(invalid_value)
        self.assertIn("Not a valid value", exc_info.exception.args[0])
        for enm in MyEnum:
            self.assertIn(enm.value, exc_info.exception.args[0], f"{enm.value} is not listed in valid enum values")

        field = fields.Enum(MyEnum, by_value=False)
        with self.assertRaises(ma.ValidationError) as exc_info:
            field._deserialize(invalid_value)
        self.assertIn("Not a valid value", exc_info.exception.args[0])
        for enm in MyEnum:
            self.assertIn(enm.name, exc_info.exception.args[0], f"{enm.name} is not listed in valid enum names")

    def test_interval_field_deserialization(self) -> None:
        # no need to test serialization, because serialization is inherited from ma's `TimeDelta` field
        for interval, expected_timedelta in [
            ("3 hours 2 minutes 3 seconds", datetime.timedelta(hours=3, minutes=2, seconds=3)),
            ("3 hours 3 seconds", datetime.timedelta(hours=3, seconds=3)),
            (86400, datetime.timedelta(seconds=86400)),
        ]:
            value = fields.Interval().deserialize(interval)
            self.assertIsInstance(value, datetime.timedelta, "Interval deserialized not in timedelta")
            self.assertEqual(value, expected_timedelta, "invalid Interval deserialization value")

    def test_interval_overflow_error(self) -> None:
        with self.assertRaises(ma.ValidationError):
            max_seconds = (datetime.timedelta.max.days + 1) * 24 * 60 * 60
            fields.Interval().deserialize(max_seconds)

    def test_interval_invalid_range_err(self) -> None:
        with self.assertRaises(ma.ValidationError):
            fields.Interval().deserialize("invalid range")

    def test_interval_zero_range_not_allowed(self) -> None:
        with self.assertRaises(ma.ValidationError):
            fields.Interval().deserialize(0)

    def test_interval_zero_range_allowed(self) -> None:
        interval: datetime.timedelta = fields.Interval(allow_zero=True).deserialize(0)
        self.assertEqual(interval.total_seconds(), 0)

    def test_ma_fields_patched_required(self) -> None:
        ma_fields = {key: value
                     for key, value in vars(fields).items()
                     if safe_issubclass(value, ma.fields.Field)}
        for key, value in ma_fields.items():
            self.assertTrue(value._rf_patched)  # noqa
            if value is fields.Nested:
                # Nested field require to pass positional argument - Schema
                field_obj = value(ma.Schema())
            elif value is fields.List:
                # List field required to pass positional argument - Field
                field_obj = value(fields.Str())
            elif value is fields.Tuple:
                # Tuple field required to pass positional argument - tuple
                field_obj = value(tuple())
            elif value is fields.Constant:
                # Tuple field required to pass positional argument - constant
                field_obj = value(1)
            elif value is fields.Pluck:
                # Pluck field required to pass two positional arguments - Schema and field_name
                field_obj = value(ma.Schema(), field_name="test")
            elif value is fields.Enum:
                field_obj = value(enum.Enum)
            else:
                field_obj = value()

            self.assertTrue(field_obj.required, (
                f"`required` default True was not patched for {value.__name__} field"
            ))

    def test_ma_fields_patched_write_read_only(self) -> None:
        class ReadWriteOnlyFieldsSerializer(Serializer):
            write = fields.Str(write_only=True)
            read = fields.Interval(read_only=True)

        serializer = ReadWriteOnlyFieldsSerializer()
        self.assertTrue(serializer.fields["write"].load_only)
        self.assertTrue(serializer.fields["read"].dump_only)
