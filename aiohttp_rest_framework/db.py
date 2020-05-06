import abc
import typing

from aiopg.sa import Engine
from aiopg.sa.result import ResultProxy, RowProxy
from sqlalchemy import Table, and_

from aiohttp_rest_framework import types
from aiohttp_rest_framework.exceptions import MultipleObjectsReturned, ObjectNotFound

__all__ = ["DatabaseServiceABC", "AioPGSAService"]


class DatabaseServiceABC(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __init__(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    async def get(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    async def all(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    async def filter(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    async def create(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    async def update(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    async def delete(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    async def execute(self, *args, **kwargs):
        pass


class AioPGSAService(DatabaseServiceABC):
    def __init__(self, connection: Engine, model: Table):
        super().__init__()
        self.connection = connection
        self.model = model

    async def get(self, **where) -> typing.Optional[RowProxy]:
        where = self._construct_whereclause(where)
        query = self.model.select(where)
        try:
            objs = await self.execute(query, fetch="all")
        except Exception:
            raise ObjectNotFound()
        if len(objs) > 1:
            raise MultipleObjectsReturned()
        if len(objs) == 0:
            raise ObjectNotFound()
        return objs[0]

    async def all(self) -> typing.List[RowProxy]:
        query = self.model.select()
        return await self.execute(query, fetch="all")

    async def filter(self, **where) -> typing.List[RowProxy]:
        where = self._construct_whereclause(where)
        query = self.model.select(where)
        return await self.execute(query, fetch="all")

    async def create(self, **data) -> RowProxy:
        query = self.model.insert().values(**data).returning(*self.model.columns)
        return await self.execute(query, fetch="one")

    async def update(self, instance: RowProxy, **data) -> RowProxy:
        pk = self._get_pk()
        where = self.model.columns[pk] == instance[pk]
        query = self.model.update(where).values(**data).returning(*self.model.columns)
        return await self.execute(query, fetch="one")

    async def delete(self, instance: RowProxy) -> ResultProxy:
        pk = self._get_pk()
        where = self.model.columns[pk] == instance[pk]
        query = self.model.delete(where)
        return await self.execute(query)

    async def execute(
            self,
            query: typing.Any,
            *,
            fetch: typing.Optional[types.Fetch] = None,
    ) -> types.ExecuteResultAioPgSA:
        async with self.connection.acquire() as conn:
            result: ResultProxy = await conn.execute(query)
            if fetch is not None:
                if fetch == "all":
                    return await result.fetchall()
                return await result.fetchone()
            return result

    def _get_pk(self) -> str:
        """
        Take first primary key even if there are many,
        it doesn't matter when we just need to get object for update/delete

        :return: `self.model`'s primary key
        """
        pks = self.model.primary_key.columns.keys()
        return pks[0]

    def _construct_whereclause(self, where):
        if where:
            return and_(self.model.columns[key] == value for key, value in where.items())
        return None
