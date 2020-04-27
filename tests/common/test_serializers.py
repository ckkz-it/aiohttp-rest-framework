import pytest

from aiohttp_rest_framework.serializers import ModelSerializer
from tests import models


def test_non_existing_field_passed_to_serializer(test_user_data: dict):
    invalid_field = "some_invalid"

    class UserSerializerWithInvalidFields(ModelSerializer):
        class Meta:
            model = models.users
            fields = ("name", "email", invalid_field)

    with pytest.raises(AssertionError, match=f"{invalid_field} was not found for"):
        UserSerializerWithInvalidFields(test_user_data)
