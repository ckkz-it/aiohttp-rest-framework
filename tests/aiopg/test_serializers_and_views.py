import asyncio

from aiohttp.test_utils import TestClient
from aiopg.sa.result import RowProxy

from tests.aiopg.utils import (
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


async def test_create_view(client: TestClient, get_last_created_user, test_user):
    response = await client.post(f"/users", json=test_user)
    assert response.status == 201, "invalid response status code"

    data = await response.json()
    assert data, "response data is empty"
    assert "id" in data, "user id isn't id data"

    user: RowProxy = await get_last_created_user()
    assert str(user.id) == data["id"], "wrong user id"
