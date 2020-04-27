import asyncio

from aiohttp.test_utils import TestClient
from aiopg.sa.result import RowProxy

from aiohttp_rest_framework.serializers import ModelSerializer
from tests import models
from tests.aiopg_sa.utils import (
    create_data_fixtures,
    create_pg_db,
    create_tables,
    drop_pg_db,
    drop_tables,
)
from tests.config import db


def setup_module():
    create_pg_db(db_name=db["database"])


def teardown_module():
    drop_pg_db(db_name=db["database"])


def setup_function():
    create_tables()
    loop = asyncio.new_event_loop()
    loop.run_until_complete(create_data_fixtures())
    loop.close()


def teardown_function():
    drop_tables()


async def test_list_view(client: TestClient):
    response = await client.get("/users")
    assert response.status == 200, "invalid response"
    data = await response.json()
    assert data, "response data is empty"
    user = data[0]
    assert user["id"]
    assert user.get("password") is None, "read only field is in serializer data"


async def test_retrieve_view(client: TestClient, user: RowProxy):
    response = await client.get(f"/users/{user.id}")
    assert response.status == 200, "invalid response"
    data = await response.json()
    assert data, "response data is empty"
    assert str(user.id) == data["id"], "got wrong user"


async def test_create_view(client: TestClient, get_last_created_user, test_user_data):
    response = await client.post("/users", json=test_user_data)
    assert response.status == 201, "invalid response status code"

    data = await response.json()
    assert data, "response data is empty"
    assert "id" in data, "user id isn't in data"

    user: RowProxy = await get_last_created_user()
    assert str(user.id) == data["id"]
    assert user.name == data["name"]
    assert user.phone == data["phone"]
    assert user.email == data["email"]


async def test_update_view(client: TestClient, user: RowProxy, get_user_by_id):
    user_data = {
        "id": str(user.id),  # serialize uuid
        "created_at": str(user.created_at),  # serialize datetime,
        "name": "Updated Name",
        "email": "updated@mail.com",
        "phone": "+7346352401",
    }
    response = await client.put(f"/users/{user.id}", json=user_data)
    assert response.status == 200, "invalid response"

    response_data = await response.json()
    updated_user = await get_user_by_id(user.id)
    assert response_data["id"] == user_data["id"], "id shouldn't change"
    assert response_data["name"] == user_data["name"] == updated_user.name
    assert response_data["email"] == user_data["email"] == updated_user.email
    assert response_data["phone"] == user_data["phone"] == updated_user.phone


async def test_partial_update_view(client: TestClient, user: RowProxy, get_user_by_id):
    user_data = {
        "email": "updated@mail.com",
    }
    response = await client.patch(f"/users/{user.id}", json=user_data)
    assert response.status == 200, "invalid response"

    response_data = await response.json()
    updated_user = await get_user_by_id(user.id)
    assert response_data["email"] == user_data["email"] == updated_user.email
    assert updated_user.email != user.email
    assert response_data["name"] == user.name, "wrong field updated"


async def test_update_non_existent_user(client: TestClient):
    response = await client.put("/users/123", json={})
    assert response.status == 404, "invalid response"


async def test_destroy_view(client: TestClient, user: RowProxy, get_user_by_id):
    response = await client.delete(f"/users/{user.id}")
    assert response.status == 204, "invalid response"

    user = await get_user_by_id(user.id)
    assert user is None, "user wasn't deleted"


async def test_destroy_non_existend_user(client: TestClient):
    response = await client.delete("/users/123")
    assert response.status == 404, "invalid response"


# use `client` here to initialize app's db connection property
async def test_fields_all_for_serializer(user: RowProxy, users_fixtures, client):
    class UserWithFieldsALLSerializer(ModelSerializer):
        class Meta:
            model = models.users
            fields = "__all__"

    serializer = UserWithFieldsALLSerializer(user)
    for field_name in serializer.data:
        assert field_name in models.users.columns, (
            f"unknown serialized field '{field_name}' for users model"
        )

    user_data = users_fixtures[0]
    user_data["email"] = "new@mail.com"  # emails are unique, change to any non existent
    serializer = UserWithFieldsALLSerializer(data=user_data)
    serializer.is_valid(raise_exception=True)
    assert serializer.validated_data
    await serializer.save()
    for field_name in serializer.data:
        assert field_name in models.users.columns, (
            f"unknown serialized field '{field_name}' for users model"
        )
