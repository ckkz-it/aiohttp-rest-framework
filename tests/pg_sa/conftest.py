import pytest
from aiohttp.test_utils import TestClient

from tests import models
from tests.pg_sa.app import get_app
from tests.pg_sa.utils import async_engine_connection


@pytest.fixture
async def user(loop):
    async with async_engine_connection() as conn:
        query = models.users.select().limit(1)
        return await conn.fetch_one(query)


@pytest.fixture
async def get_last_created_user(loop):
    async def _get_last_user():
        async with async_engine_connection() as conn:
            query = models.users.select().order_by(models.users.c.created_at.desc()).limit(1)
            return await conn.fetch_one(query)

    return _get_last_user


@pytest.fixture
async def get_user_by_id(loop):
    async def _get_user_by_id(user_id):
        async with async_engine_connection() as conn:
            query = models.users.select(models.users.c.id == user_id)
            return await conn.fetch_one(query)

    return _get_user_by_id


@pytest.fixture
async def client(aiohttp_client):
    client: TestClient = await aiohttp_client(get_app())
    return client


@pytest.fixture
async def pg_sa_instance(loop):
    async with async_engine_connection() as conn:
        query = models.pg_sa_fields.select().limit(1)
        return await conn.fetch_one(query)


def pytest_runtest_setup(item):
    if "with_client" in item.keywords and "client" not in item.fixturenames:
        # inject client
        item.fixturenames.append("client")
