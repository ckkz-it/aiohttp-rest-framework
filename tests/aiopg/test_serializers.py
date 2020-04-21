from aiohttp import web
from aiohttp.test_utils import TestClient

from tests.aiopg.app import app


async def test_first(aiohttp_client):
    client: TestClient = await aiohttp_client(app)
    response = await client.get("/user")
    print(await response.json())
