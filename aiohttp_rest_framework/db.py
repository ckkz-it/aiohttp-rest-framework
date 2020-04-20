import abc

import typing

from aiopg.sa import Engine
from aiopg.sa.result import ResultProxy, RowProxy
from sqlalchemy import Table
from sqlalchemy.sql.elements import BinaryExpression, BooleanClauseList

from aiohttp_rest_framework import types


class DatabaseServiceABC(metaclass=abc.ABCMeta):
    def __init__(self, connection):
        self.connection = connection

    @abc.abstractmethod
    async def create(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    async def update(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    async def delete(self, *args, **kwargs):
        pass


class PostgresService(DatabaseServiceABC):
    connection: Engine = None
    db_table: Table = None

    def __init__(self, connection: Engine, db_table: Table = None):
        super().__init__(connection)
        self.db_table = db_table

    async def create(
            self,
            data: dict,
            *,
            return_created_obj: bool = False,
    ) -> typing.Optional[RowProxy]:
        query = self.db_table.insert().values(**data)
        if return_created_obj:
            query = query.returning(*self.db_table.columns)
        return await self.execute(query, fetch='one')

    async def update(
            self,
            data: dict,
            where: typing.Union[BinaryExpression, BooleanClauseList] = None,
    ) -> ResultProxy:
        query = self.db_table.update(where).values(**data)
        return await self.execute(query)

    async def delete(self, pk: typing.Any, *, pk_field: str = 'id'):
        query = self.db_table.delete(**{pk_field: pk})
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
