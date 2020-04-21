import aiopg.sa
from aiohttp import web

from aiohttp_rest_framework.settings import setup_rest_framework
from tests.routes import setup_routes
from tests.config import postgres_url


async def init_pg(a: web.Application) -> None:
    a["db"] = await aiopg.sa.create_engine(postgres_url)


async def close_pg(a: web.Application) -> None:
    a["db"].close()
    await a["db"].wait_closed()


async def get_app():
    app = web.Application()
    setup_routes(app)
    setup_rest_framework(app)
    app.on_startup.append(init_pg)
    app.on_cleanup.append(close_pg)
    return app
