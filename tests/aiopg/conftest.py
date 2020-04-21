import pytest
from aiohttp.test_utils import TestClient
from aiopg.sa.result import ResultProxy

from tests import models
from tests.aiopg.app import get_app
from tests.aiopg.utils import async_engine_connection


@pytest.fixture
async def user():
    async with async_engine_connection() as engine:
        async with engine.acquire() as conn:
            query = models.users.select().limit(1)
            result: ResultProxy = await conn.execute(query)
            yield await result.fetchone()


@pytest.fixture
async def client(aiohttp_client):
    client: TestClient = await aiohttp_client(await get_app())
    yield client
