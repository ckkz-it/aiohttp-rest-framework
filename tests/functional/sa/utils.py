import json
import pathlib
from typing import List

from sqlalchemy import MetaData

from tests.utils import async_engine_connection


def get_fixtures_data():
    file = pathlib.Path(__file__).parent / "fixtures.json"
    with open(file) as f:
        return json.loads(f.read())


def get_fixtures_by_name(name: str) -> List[dict]:
    return get_fixtures_data()[name]


async def create_tables(metadata: MetaData, db_url: str):
    async with async_engine_connection(db_url) as connection:
        await connection.run_sync(metadata.create_all)


async def drop_tables(metadata: MetaData, db_url: str):
    async with async_engine_connection(db_url) as connection:
        await connection.run_sync(metadata.drop_all)
