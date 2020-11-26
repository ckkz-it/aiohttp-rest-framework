import json

from aiohttp.test_utils import unittest_run_loop

from aiohttp_rest_framework import fields
from aiohttp_rest_framework.exceptions import ValidationError
from aiohttp_rest_framework.serializers import ModelSerializer, Serializer
from tests.functional.sa.core.base import BaseTestCase
from tests.test_app.sa.core import models
from tests.test_app.sa.core.serializers import UserSerializer


class SerializerTestCase(BaseTestCase):
    @unittest_run_loop
    async def test_fields_all_for_serializer(self):
        class UserWithFieldsALLSerializer(ModelSerializer):
            company_id = fields.Str(required=False)

            class Meta:
                model = models.User
                fields = "__all__"

        serializer = UserWithFieldsALLSerializer(self.user)
        for field_name in serializer.data:
            assert field_name in models.User.columns, (
                f"unknown serialized field '{field_name}' for users model"
            )

        serializer = UserWithFieldsALLSerializer(data=self.get_test_user_data())
        serializer.is_valid(raise_exception=True)
        assert serializer.validated_data
        await serializer.save()
        for field_name in serializer.data:
            assert field_name in models.User.columns, (
                f"unknown serialized field '{field_name}' for users model"
            )

    @unittest_run_loop
    async def test_serializer_is_valid_empty_data(self) -> None:
        with self.assertRaises(ValidationError) as exc_info:
            UserSerializer(data="").is_valid()
        self.assertEqual(json.loads(exc_info.exception.text), {"error": "No data provided"})

    def test_non_existing_model_field_passed_to_serializer(self) -> None:
        invalid_field = "invalid_field"

        class UserSerializerWithInvalidFields(ModelSerializer):
            class Meta:
                model = models.User
                fields = ("name", "email", invalid_field)

        with self.assertRaises(AssertionError) as exc_info:
            UserSerializerWithInvalidFields(self.get_test_user_data())
        self.assertIn(f"{invalid_field} was not found for", exc_info.exception.args[0])

    def test_non_existing_model_field_but_defined_in_serializer(self) -> None:
        invalid_field = "invalid_field"
        field_cls = fields.Str

        class UserSerializer(ModelSerializer):
            invalid_field = field_cls()

            class Meta:
                model = models.User
                fields = ("name", "email", invalid_field)

        serializer = UserSerializer(self.get_test_user_data())
        self.assertIn(invalid_field, serializer.fields)
        self.assertIsInstance(serializer.fields[invalid_field], field_cls)

    class SomeSerializer(Serializer):
        pass

    @unittest_run_loop
    async def test_serializer_update_create_not_implemented(self) -> None:
        with self.assertRaises(NotImplementedError) as exc_info:
            await self.SomeSerializer().create(...)
        self.assertIn("create()", exc_info.exception.args[0])

        with self.assertRaises(NotImplementedError) as exc_info:
            await self.SomeSerializer().update(..., ...)
        self.assertIn("update()", exc_info.exception.args[0])

    def test_serializer_data_attr_called_invalid(self):
        with self.assertRaises(AssertionError) as exc_info:
            _ = self.SomeSerializer(data={}).data
        self.assertIn("must call `.is_valid()", exc_info.exception.args[0])

    def test_serializer_errors_attr_called_invalid(self) -> None:
        with self.assertRaises(AssertionError) as exc_info:
            _ = self.SomeSerializer().errors
        self.assertIn("must call `.is_valid()", exc_info.exception.args[0])

    def test_serializer_validated_data_attr_called_invalid(self) -> None:
        with self.assertRaises(AssertionError) as exc_info:
            _ = self.SomeSerializer().validated_data
        self.assertIn("must call `.is_valid()", exc_info.exception.args[0])

    class DataAttrSerializer(Serializer):
        test = fields.Int()

    def test_serializer_data_attr_with_initial_data(self) -> None:
        serializer = self.DataAttrSerializer(data={"test": 123})
        serializer.is_valid(raise_exception=True)
        _ = serializer.data

    def test_serializer_data_attr_with_instance_and_errors(self) -> None:
        serializer = self.DataAttrSerializer(instance={"test": 123}, data={"test": "not an integer"})
        serializer.is_valid()
        _ = serializer.data
        self.assertTrue(serializer.errors)
        self.assertIn("test", serializer.errors)

    def test_serializer_field_inheritance(self) -> None:
        class BaseSerializer(Serializer):
            field_one = fields.Int()
            fields_two = fields.Str()

        class InheritSerializer(BaseSerializer):
            pass

        serializer = InheritSerializer()
        self.assertEqual(len(serializer.fields), len(BaseSerializer().fields))

    def test_serializer_fields_all_and_custom_field(self) -> None:
        class Ser(ModelSerializer):
            custom = fields.Str()

            class Meta:
                model = models.User
                fields = "__all__"

        serializer = Ser()
        self.assertIn("custom", serializer.fields)
        self.assertEqual(len(models.User.columns) + 1, len(serializer.fields))


class AsyncConnectionPassedToConfigTestCase(BaseTestCase):
    @staticmethod
    async def get_conn():
        return "some connection"

    def setUp(self) -> None:
        self.rest_config = {"get_connection": self.get_conn}
        super().setUp()

    @unittest_run_loop
    async def test_success(self) -> None:
        class ForConnectionSerializer(ModelSerializer):
            class Meta:
                model = models.User
                fields = "__all__"

        db_manager = await ForConnectionSerializer().get_db_manager()
        self.assertIs(await db_manager.get_engine(), await self.get_conn())
