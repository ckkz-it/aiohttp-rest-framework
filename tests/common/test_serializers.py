import pytest
from marshmallow import fields

from aiohttp_rest_framework.serializers import ModelSerializer, Serializer
from tests import models
from tests.base_app import get_base_app


def test_non_existing_field_passed_to_serializer(test_user_data: dict):
    invalid_field = "some_invalid"

    class UserSerializerWithInvalidFields(ModelSerializer):
        class Meta:
            model = models.users
            fields = ("name", "email", invalid_field)

    with pytest.raises(AssertionError, match=f"{invalid_field} was not found for"):
        UserSerializerWithInvalidFields(test_user_data)


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
    serializer.is_valid(raise_exception=False)
    _ = serializer.data
