from tests.aiopg.app import app


async def test_first(aiohttp_client):
    client = await aiohttp_client(app)
    response = await client.get('/foo')
