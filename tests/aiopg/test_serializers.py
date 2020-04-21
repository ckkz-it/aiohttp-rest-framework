from aiohttp.test_utils import TestClient
from aiopg.sa.result import RowProxy

from tests.aiopg.app import get_app
from tests.aiopg.utils import (
    create_data_fixtures, create_tables, drop_tables, create_pg_db,
    drop_pg_db,
)
from tests.config import db


def setup_module():
    create_pg_db(db_name=db["database"])


def teardown_module():
    drop_pg_db(db_name=db["database"])


def setup_function():
    create_tables()
    create_data_fixtures()


def teardown_function():
    drop_tables()


async def test_list_model_serializer(client: TestClient):
    response = await client.get("/users")
    data = await response.json()
    assert data, "response data is empty"
    user = data[0]
    assert user["id"]
    assert user.get("password") is None, "read only field is in serializer"


async def test_retrieve_model_serializer(client: TestClient, user: RowProxy):
    response = await client.get(f"/users/{user.id}")
    data = await response.json()
    assert data, "response data is empty"
    assert str(user.id) == data["id"], "got wrong user"
