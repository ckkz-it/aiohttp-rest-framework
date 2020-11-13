import inspect
from typing import Dict, Generic, Optional, Tuple, TypeVar

import sqlalchemy as sa
from databases import Database
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import create_async_engine

__all__ = (
    "ClassLookupDict",
    "get_model_fields_sa",
    "safe_issubclass",
    "create_connection",
    "create_tables",
    "drop_tables",
)

C1 = TypeVar("C1")
C2 = TypeVar("C2")


class ClassLookupDict(Generic[C1, C2]):
    """
    Takes a dictionary with classes as keys.
    Lookups against this object will traverses the object's inheritance
    hierarchy in method resolution order, and returns the first matching value
    from the dictionary.
    """

    def __init__(self, mapping: Dict[C1, C2]):
        self.mapping = mapping

    def __getitem__(self, key) -> C2:
        base_class = key.__class__
        for cls in inspect.getmro(base_class):
            if cls in self.mapping:
                return self.mapping[cls]
        raise KeyError(f"Class {key.__name__} not found in lookup.")

    def __setitem__(self, key, value) -> None:
        self.mapping[key] = value

    def get(self, key: C1, default=None) -> Optional[C2]:
        try:
            return self.__getitem__(key)
        except KeyError:
            return default

    def __reversed__(self):
        return self.__class__({value: key for key, value in self.mapping.items()})

    def __contains__(self, item) -> bool:
        try:
            self.__getitem__(item)
            return True
        except KeyError:
            return False


def get_model_fields_sa(model: sa.Table) -> Tuple[str]:
    return tuple(str(column.name) for column in model.columns)


def safe_issubclass(first, other) -> bool:
    try:
        return issubclass(first, other)
    except TypeError:
        return False


async def create_connection(dsn: str, **kwargs) -> Database:
    from aiohttp_rest_framework.settings import PG_SA, get_global_config

    config = get_global_config()
    if config.schema_type == PG_SA:
        database = Database(dsn, **kwargs)
        await database.connect()
        return database
    raise NotImplementedError()


async def create_tables(db_url: str, metadata: MetaData) -> None:
    engine = create_async_engine(db_url)
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)


async def drop_tables(db_url: str, metadata: MetaData) -> None:
    engine = create_async_engine(db_url)
    async with engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)
