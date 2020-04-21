import pytest
from aiopg.sa.result import ResultProxy

from tests import models
from tests.aiopg.utils import async_engine_connection


@pytest.fixture
async def user():
    async with async_engine_connection() as engine:
        async with engine.acquire() as conn:
            query = models.users.select().limit(1)
            result: ResultProxy = await conn.execute(query)
            yield await result.fetchone()
