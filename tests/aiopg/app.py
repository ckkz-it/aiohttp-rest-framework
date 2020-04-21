import aiopg.sa
import typing
from aiohttp import web

from tests.base_app import get_base_app
from tests.config import postgres_url


async def init_pg(a: web.Application) -> None:
    a["db"] = await aiopg.sa.create_engine(postgres_url)


async def close_pg(a: web.Application) -> None:
    a["db"].close()
    await a["db"].wait_closed()


def get_app(rest_config: typing.Mapping = None):
    app = get_base_app(rest_config=rest_config)
    app.on_startup.append(init_pg)
    app.on_cleanup.append(close_pg)
    return app
