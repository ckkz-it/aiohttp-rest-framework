import aiopg.sa
from aiohttp import web

from aiohttp_rest_framework.settings import setup_rest_framework
from tests.config import postgres_url, db
from tests.utils import create_db


async def init_pg(app: web.Application) -> None:
    create_db(db["database"])
    app["db"] = await aiopg.sa.create_engine(postgres_url)


async def close_pg(app: web.Application) -> None:
    app["db"].close()
    await app["db"].wait_closed()


app = web.Application()
setup_rest_framework(app)
app.on_startup.append(init_pg)
app.on_cleanup.append(close_pg)
