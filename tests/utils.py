import psycopg2

from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from tests.config import db


def create_db(db_name: str):
    conn = psycopg2.connect(
        dbname=db["default_database"], user=db["user"], host=db["host"], password=db["password"]
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT);
    cursor = conn.cursor()

    drop_sql = f"DROP DATABASE IF EXISTS {db_name};"
    cursor.execute(drop_sql)

    create_sql = f"CREATE DATABASE {db_name};"
    cursor.execute(create_sql)

    cursor.close()
    conn.close()
