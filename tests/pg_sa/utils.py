from contextlib import asynccontextmanager, contextmanager
from datetime import datetime

import sqlalchemy as sa
from databases import Database
from databases.core import Connection
from sqlalchemy import select

from aiohttp_rest_framework.fields import Interval
from tests import models
from tests.config import db, db_url, url_template
from tests.models import meta
from tests.utils import get_fixtures_data


@contextmanager
def sync_engine() -> sa.engine.Engine:
    engine = sa.create_engine(db_url)
    try:
        yield engine
    finally:
        engine.dispose()


async def get_async_engine(db_url_: str = db_url) -> Database:
    database = Database(db_url_)
    await database.connect()
    return database


@asynccontextmanager
async def async_engine_connection(db_url_: str = db_url) -> Connection:
    database = await get_async_engine(db_url_)
    try:
        async with database.connection() as conn:
            yield conn
    finally:
        await database.disconnect()


async def create_db(db_name: str):
    db_conf = {**db, "database": db["default_database"]}
    db_url_ = url_template.format(**db_conf)

    drop_sql = f"DROP DATABASE IF EXISTS {db_name};"
    create_sql = f"CREATE DATABASE {db_name};"
    async with async_engine_connection(db_url_) as conn:
        await conn.execute(drop_sql)
        await conn.execute(create_sql)


async def drop_db(db_name: str):
    db_conf = {**db, "database": db["default_database"]}
    db_url_ = url_template.format(**db_conf)

    drop_sql = f"DROP DATABASE IF EXISTS {db_name};"
    async with async_engine_connection(db_url_) as conn:
        await conn.execute(drop_sql)


def create_tables():
    with sync_engine() as engine:
        meta.create_all(bind=engine)


def drop_tables():
    with sync_engine() as engine:
        meta.drop_all(bind=engine)


async def create_data_fixtures():
    data = get_fixtures_data()
    async with async_engine_connection() as conn:
        for table_name, table_data in data.items():
            table: sa.Table = getattr(models, table_name)
            for td in table_data:
                if "Date" in td:
                    td["Date"] = datetime.strptime(td["Date"], "%Y-%m-%d").date()
                if "DateTime" in td:
                    td["DateTime"] = datetime.strptime(td["DateTime"], "%Y-%m-%d %H:%M:%S")
                if "Time" in td:
                    td["Time"] = datetime.strptime(td["Time"], "%H:%M:%S")
                if "Interval" in td:
                    td["Interval"] = Interval().deserialize(td["Interval"])

                await conn.execute(table.insert(td))

        company_query = select([models.companies.c.id]).limit(1)
        company = await conn.fetch_one(company_query)
        await conn.execute(models.users.update(), {"company_id": company["id"]})
