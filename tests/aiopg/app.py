import aiopg.sa
from aiohttp import web

from tests.base_app import get_base_app
from tests.config import postgres_url


async def init_pg(a: web.Application) -> None:
    a["db"] = await aiopg.sa.create_engine(postgres_url)


async def close_pg(a: web.Application) -> None:
    a["db"].close()
    await a["db"].wait_closed()


async def get_app():
    app = get_base_app()
    app.on_startup.append(init_pg)
    app.on_cleanup.append(close_pg)
    return app
