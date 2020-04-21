from contextlib import contextmanager

import psycopg2
import sqlalchemy as sa
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from tests.config import db, postgres_url
from tests.models import meta


@contextmanager
def pg_connection():
    conn = psycopg2.connect(
        dbname=db["default_database"], user=db["user"], host=db["host"], password=db["password"]
    )
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


def create_tables():
    # use sync engine here because `aiopg.sa` Engine doesn't support `create_all`
    sync_engine = sa.create_engine(postgres_url)
    meta.create_all(bind=sync_engine)
    sync_engine.dispose()  # now disconnect
