import abc

import typing

from aiopg.sa import Engine
from aiopg.sa.result import ResultProxy, RowProxy
from sqlalchemy import Table

from aiohttp_rest_framework import types


class DatabaseServiceABC(metaclass=abc.ABCMeta):
    def __init__(self, connection, model=None):
        self.connection = connection
        self.model = model

    @abc.abstractmethod
    async def create(self, data: typing.Mapping):
        pass

    @abc.abstractmethod
    async def update(self, pk: typing.Any, data: typing.Mapping):
        pass

    @abc.abstractmethod
    async def delete(self, pk: typing.Any):
        pass


class AioPGService(DatabaseServiceABC):
    connection: Engine
    model: Table

    async def create(self, data: typing.Mapping) -> RowProxy:
        query = self.model.insert().values(**data).returning(*self.model.columns)
        return await self.execute(query, fetch="one")

    async def update(
            self,
            pk: typing.Any,
            data: typing.Mapping,
            *,
            pk_field: str = "id",
    ) -> RowProxy:
        where = {pk_field: pk}
        query = self.model.update(**where).values(**data)
        await self.execute(query)
        return await self.execute(self.model.select(**where), fetch="one")

    async def delete(self, pk: typing.Any, *, pk_field: str = "id") -> ResultProxy:
        query = self.model.delete(**{pk_field: pk})
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
                if fetch == 'all':
                    return await result.fetchall()
                return await result.fetchone()
            return result
