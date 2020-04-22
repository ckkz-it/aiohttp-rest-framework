from contextlib import asynccontextmanager, contextmanager

import aiopg.sa
import psycopg2
import sqlalchemy as sa
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from tests import models
from tests.config import db, postgres_url, postgres_url_template
from tests.models import meta
from tests.utils import get_fixtures_data


@contextmanager
def pg_connection():
    db_conf = {**db, "database": db["default_database"]}
    db_url = postgres_url_template.format(**db_conf)
    conn = psycopg2.connect(db_url)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    try:
        yield cursor
    finally:
        cursor.close()
        conn.close()


def create_pg_db(db_name: str):
    drop_sql = f"DROP DATABASE IF EXISTS {db_name};"
    create_sql = f"CREATE DATABASE {db_name};"
    with pg_connection() as cursor:
        cursor.execute(drop_sql)
        cursor.execute(create_sql)


def drop_pg_db(db_name: str):
    drop_sql = f"DROP DATABASE IF EXISTS {db_name};"
    with pg_connection() as cursor:
        cursor.execute(drop_sql)


@contextmanager
def sync_engine_connection() -> sa.engine.Engine:
    engine = sa.create_engine(postgres_url)
    try:
        yield engine
    finally:
        engine.dispose()


@asynccontextmanager
async def async_engine_connection():
    engine: aiopg.sa.Engine = await aiopg.sa.create_engine(postgres_url)
    try:
        async with engine.acquire() as conn:
            yield conn
    finally:
        engine.close()


def create_tables():
    # use sync engine here because `aiopg.sa` Engine doesn't support `create_all`
    with sync_engine_connection() as engine:
        meta.create_all(bind=engine)


def drop_tables():
    with sync_engine_connection() as engine:
        meta.drop_all(bind=engine)


async def create_data_fixtures():
    data = get_fixtures_data()
    async with async_engine_connection() as conn:
        for table_name, table_data in data.items():
            table: sa.Table = getattr(models, table_name)
            await conn.execute(table.insert().values(table_data))
