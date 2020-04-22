import abc
import typing

from aiopg.sa import Engine
from aiopg.sa.result import ResultProxy, RowProxy
from sqlalchemy import Table, and_

from aiohttp_rest_framework import types


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
        return await self.execute(query, fetch="one")

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
        pk = self.get_pk()
        where = self.model.columns[pk] == instance[pk]
        query = self.model.update(where).values(**data)
        await self.execute(query)
        return await self.execute(self.model.select(where), fetch="one")

    async def delete(self, instance: RowProxy) -> ResultProxy:
        pk = self.get_pk()
        where = self.model.columns[pk] == instance[pk]
        query = self.model.delete(where)
        return await self.execute(query)

    async def execute(
            self,
            query: typing.Any,
            *,
            fetch: typing.Optional[types.Fetch] = None,
    ) -> types.ExecuteResultAioPg:
        async with self.connection.acquire() as conn:
            result: ResultProxy = await conn.execute(query)
            if fetch is not None:
                if fetch == "all":
                    return await result.fetchall()
                return await result.fetchone()
            return result

    def get_pk(self):
        return self.model.primary_key.columns.keys()[0]
