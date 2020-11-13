import asyncio
import json

import pytest
from aiohttp.test_utils import TestClient

from aiohttp_rest_framework import fields
from aiohttp_rest_framework.exceptions import ValidationError
from aiohttp_rest_framework.serializers import ModelSerializer
from tests import models
from tests.config import db
from tests.pg_sa.utils import create_data_fixtures, create_db, create_tables, drop_db, drop_tables
from tests.serializers import UserSerializer


def setup_module():
    loop = asyncio.new_event_loop()
    loop.run_until_complete(create_db(db_name=db["database"]))
    loop.close()


def teardown_module():
    loop = asyncio.new_event_loop()
    loop.run_until_complete(drop_db(db_name=db["database"]))
    loop.close()


def setup_function():
    create_tables()
    loop = asyncio.new_event_loop()
    loop.run_until_complete(create_data_fixtures())
    loop.close()


def teardown_function():
    drop_tables()


@pytest.mark.with_client
async def test_fields_all_for_serializer(user, test_user_data):
    class UserWithFieldsALLSerializer(ModelSerializer):
        company_id = fields.Str(required=False)

        class Meta:
            model = models.users
            fields = "__all__"

    serializer = UserWithFieldsALLSerializer(user)
    for field_name in serializer.data:
        assert field_name in models.users.columns, (
            f"unknown serialized field '{field_name}' for users model"
        )

    serializer = UserWithFieldsALLSerializer(data=test_user_data)
    serializer.is_valid(raise_exception=True)
    assert serializer.validated_data
    await serializer.save()
    for field_name in serializer.data:
        assert field_name in models.users.columns, (
            f"unknown serialized field '{field_name}' for users model"
        )


async def test_serializer_is_valid_empty_data(client: TestClient):
    with pytest.raises(ValidationError, match="Bad Request") as exc_info:
        UserSerializer(data="").is_valid()
    assert json.loads(exc_info.value.text) == {"error": "No data provided"}, "Wrong error caught"
