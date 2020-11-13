import asyncio
import uuid

import pytest
from aiohttp.test_utils import TestClient

from tests.config import db
from tests.pg_sa.utils import create_data_fixtures, create_db, create_tables, drop_db, drop_tables


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


async def test_validation_error_exception(client: TestClient, user):
    user_data = {
        "phone": "1111",
    }
    response = await client.put(f"/users/{user['id']}", json=user_data)
    assert response.status == 400
    assert response.content_type == "application/json"
    err = await response.json()
    assert "email" in err, "wrong error caught"


@pytest.mark.parametrize("non_existing_id", [uuid.uuid4(), "123", "non_existing"])
async def test_not_found_exception(client: TestClient, non_existing_id):
    response = await client.get(f"/users/{non_existing_id}")
    assert response.status == 404
    assert response.content_type == "application/json"
