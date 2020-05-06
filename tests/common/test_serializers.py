import marshmallow as ma
import pytest

from aiohttp_rest_framework import fields
from aiohttp_rest_framework.serializers import ModelSerializer, Serializer
from tests import models
from tests.base_app import get_base_app
from tests.serializers import UserSerializer


def test_non_existing_model_field_passed_to_serializer(test_user_data: dict):
    invalid_field = "invalid_field"

    class UserSerializerWithInvalidFields(ModelSerializer):
        class Meta:
            model = models.users
            fields = ("name", "email", invalid_field)

    with pytest.raises(AssertionError, match=f"{invalid_field} was not found for"):
        UserSerializerWithInvalidFields(test_user_data)


def test_non_existing_model_field_but_defined_in_serializer(test_user_data: dict):
    invalid_field = "invalid_field"

    class UserSerializer(ModelSerializer):
        invalid_field = ma.fields.Str()

        class Meta:
            model = models.users
            fields = ("name", "email", invalid_field)

    serializer = UserSerializer(test_user_data)
    assert invalid_field in serializer.fields
    assert isinstance(serializer.fields[invalid_field], ma.fields.Str)


async def test_async_get_connection_passed_to_config():
    async def get_conn():
        return "some connection"

    class ForConnectionSerializer(ModelSerializer):
        class Meta:
            model = models.users
            fields = "__all__"

    rest_config = {"get_connection": get_conn}
    get_base_app(rest_config)  # init app with config
    db_service = await ForConnectionSerializer().get_db_service()
    assert db_service.connection is await get_conn()


class SomeSerializer(Serializer):
    pass


async def test_serializer_update_create_not_implemented():
    with pytest.raises(NotImplementedError, match="create()"):
        await SomeSerializer().create(...)

    with pytest.raises(NotImplementedError, match="update()"):
        await SomeSerializer().update(..., ...)


def test_serializer_data_attr_called_invalid():
    with pytest.raises(AssertionError, match="must call `.is_valid()"):
        _ = SomeSerializer(data={}).data


def test_serializer_errors_attr_called_invalid():
    with pytest.raises(AssertionError, match="must call `.is_valid()"):
        _ = SomeSerializer().errors


def test_serializer_validated_data_attr_called_invalid():
    with pytest.raises(AssertionError, match="must call `.is_valid()"):
        _ = SomeSerializer().validated_data


class DataAttrSerializer(Serializer):
    test = fields.Int()


def test_serializer_data_attr_with_initial_data():
    serializer = DataAttrSerializer(data={"test": 123})
    serializer.is_valid(raise_exception=True)
    _ = serializer.data


def test_serializer_data_attr_with_instance_and_errors():
    serializer = DataAttrSerializer(instance={"test": 123}, data={"test": "not an integer"})
    serializer.is_valid()
    _ = serializer.data
    assert serializer.errors
    assert "test" in serializer.errors


def test_serializer_field_inheritance():
    class InheritSerializer(UserSerializer):
        pass

    serializer = InheritSerializer()
    assert serializer.opts.model is not None
    assert len(serializer.fields) == len(UserSerializer().fields)


def test_serializer_fields_all_and_custom_field():
    class Ser(ModelSerializer):
        custom = fields.Constant(5)

        class Meta:
            model = models.users
            fields = "__all__"

    serializer = Ser()
    assert "custom" in serializer.fields
    assert len(models.users.columns) + 1 == len(serializer.fields)
