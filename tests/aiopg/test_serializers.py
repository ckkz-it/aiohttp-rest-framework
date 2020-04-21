from aiohttp.test_utils import TestClient

from tests.aiopg.app import app
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


async def test_retrieve_model_serializer(aiohttp_client):
    client: TestClient = await aiohttp_client(app)
    response = await client.get("/users")
    data = await response.json()
    assert data, "response data is empty"
    user = data[0]
    assert user["id"]
    assert user.get("password") is None, "read only field is in serializer"
