from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, AsyncSession, create_async_engine


def get_engine(db_url: str) -> AsyncEngine:
    return create_async_engine(db_url)


@asynccontextmanager
async def async_engine_connection(db_url: str) -> AsyncConnection:
    engine = get_engine(db_url)
    try:
        async with engine.begin() as conn:
            yield conn
    finally:
        await engine.dispose()


@asynccontextmanager
async def async_session(db_url: str) -> AsyncSession:
    engine = get_engine(db_url)
    try:
        async with AsyncSession(engine, expire_on_commit=False) as session:
            async with session.begin():
                yield session
    finally:
        await session.commit()
        await engine.dispose()


async def create_db(default_db_url: str, db_name: str):
    await drop_db(default_db_url, db_name)
    create_sql = text(f"CREATE DATABASE {db_name};")
    async with async_engine_connection(default_db_url) as conn:
        await conn.execute(create_sql)


async def drop_db(default_db_url: str, db_name: str):
    drop_sql = text(f"DROP DATABASE IF EXISTS {db_name};")
    async with async_engine_connection(default_db_url) as conn:
        await conn.execute(drop_sql)
