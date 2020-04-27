import asyncio
import uuid

import pytest
from aiohttp.test_utils import TestClient
from aiopg.sa.result import RowProxy

from tests.aiopg_sa.utils import create_data_fixtures, create_pg_db, create_tables, drop_pg_db
from tests.config import db


def setup_module():
    create_pg_db(db_name=db["database"])
    create_tables()
    loop = asyncio.new_event_loop()
    loop.run_until_complete(create_data_fixtures())
    loop.close()


def teardown_module():
    drop_pg_db(db_name=db["database"])


async def test_validation_error_exception(client: TestClient, user: RowProxy):
    user_data = {
        "phone": "1111",
    }
    response = await client.put(f"/users/{user.id}", json=user_data)
    assert response.status == 400
    assert response.content_type == "application/json"
    err = await response.json()
    assert "email" in err, "wrong error caught"


@pytest.mark.parametrize("non_existing_id", [uuid.uuid4(), "123", "non_existing"])
async def test_not_found_exception(client: TestClient, non_existing_id):
    response = await client.get(f"/users/{non_existing_id}")
    assert response.status == 404
    assert response.content_type == "application/json"
