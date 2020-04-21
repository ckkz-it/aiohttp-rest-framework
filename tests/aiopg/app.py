import aiopg.sa
from aiohttp import web

from aiohttp_rest_framework.settings import setup_rest_framework
from tests.routes import setup_routes
from tests.config import db, postgres_url
from tests.utils import create_pg_db, create_tables, drop_pg_db


async def init_pg(a: web.Application) -> None:
    create_pg_db(db["database"])
    create_tables()
    a["db"] = await aiopg.sa.create_engine(postgres_url)


async def close_pg(a: web.Application) -> None:
    a["db"].close()
    await a["db"].wait_closed()
    drop_pg_db(db["database"])


app = web.Application()
setup_routes(app)
setup_rest_framework(app)
app.on_startup.append(init_pg)
app.on_cleanup.append(close_pg)
