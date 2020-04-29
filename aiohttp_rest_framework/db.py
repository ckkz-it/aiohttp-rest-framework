import abc
import typing

from aiopg.sa import Engine
from aiopg.sa.result import ResultProxy, RowProxy
from sqlalchemy import Table, and_

from aiohttp_rest_framework import types
from aiohttp_rest_framework.exceptions import ObjectNotFound

__all__ = ["DatabaseServiceABC", "AioPGSAService"]


class DatabaseServiceABC(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __init__(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    async def get(self, *args, **kwargs):
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


class AioPGSAService(DatabaseServiceABC):
    def __init__(self, connection: Engine, model: Table):
        super().__init__()
        self.connection = connection
        self.model = model

    async def get(self, where: typing.Mapping = None) -> typing.Optional[RowProxy]:
        if where:
            where = and_(self.model.columns[key] == value for key, value in where.items())

        query = self.model.select(where).limit(1)
        try:
            obj = await self.execute(query, fetch="one")
        except Exception:
            raise ObjectNotFound()
        if obj is None:
            raise ObjectNotFound()
        return obj

    async def filter(self, where: typing.Mapping = None) -> typing.List[RowProxy]:
        if where:
            where = and_(self.model.columns[key] == value for key, value in where.items())

        query = self.model.select(where)
        return await self.execute(query, fetch="all")

    async def create(self, data: typing.Mapping) -> RowProxy:
        query = self.model.insert().values(**data).returning(*self.model.columns)
        return await self.execute(query, fetch="one")

    async def update(
            self,
            instance: RowProxy,
            data: typing.Mapping,
    ) -> RowProxy:
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
        Take any (first) primary key even if there are many,
        it doesn't matter when we just need to get object for update/delete

        :return: `self.model`'s primary key
        """
        pks = self.model.primary_key.columns.keys()
        return pks[0]
