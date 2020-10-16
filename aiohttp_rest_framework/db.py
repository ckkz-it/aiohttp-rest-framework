import abc
from typing import Any, List, Optional, Union

from aiopg.sa import Engine
from aiopg.sa.result import ResultProxy, RowProxy
from psycopg2 import Error as PsycopgError
from sqlalchemy import (
    Table,
    and_,
    bindparam,
    delete,
    insert,
    literal_column,
    not_,
    or_,
    select,
    update,
)
from sqlalchemy.sql.elements import BindParameter, BooleanClauseList, ColumnClause, literal

from aiohttp_rest_framework import types
from aiohttp_rest_framework.exceptions import (
    DatabaseException,
    FieldValidationError,
    MultipleObjectsReturned,
    ObjectNotFound,
    UniqueViolationError,
)

__all__ = ["DatabaseServiceABC", "AioPGSAService", "operation", "op"]


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

    async def get(
        self,
        whereclause: Optional[BooleanClauseList] = None,
        params=None,
        **inline_kwargs
    ) -> Optional[RowProxy]:
        if whereclause is None:
            whereclause = self._construct_whereclause(inline_kwargs)
        query = select([self.model], whereclause)
        try:
            objs = await self.execute(query, fetch="all", params=params)
        except DatabaseException:
            raise ObjectNotFound()
        if len(objs) > 1:
            raise MultipleObjectsReturned()
        if len(objs) == 0:
            raise ObjectNotFound()
        return objs[0]

    async def all(self) -> List[RowProxy]:
        query = select([self.model])
        return await self.execute(query, fetch="all")

    async def filter(
        self,
        whereclause: Optional[BooleanClauseList] = None,
        params=None,
        **inline_kwargs
    ) -> List[RowProxy]:
        if whereclause is None:
            whereclause = self._construct_whereclause(inline_kwargs)
        query = select([self.model], whereclause)
        return await self.execute(query, params=params, fetch="all")

    async def create(self, **data) -> RowProxy:
        query = insert(self.model, data).returning(literal_column("*"))
        return await self.execute(query, fetch="one")

    async def update(
        self,
        instance: RowProxy,
        whereclause: Optional[BooleanClauseList] = None,
        params: Optional[dict] = None,
        **data,
    ) -> RowProxy:
        if whereclause is None:
            pk = self._get_pk()
            whereclause = self.model.columns[pk] == instance[pk]
        query = update(self.model, whereclause, data).returning(literal_column("*"))
        return await self.execute(query, params=params, fetch="one")

    async def delete(
        self,
        instance: RowProxy,
        whereclause: Optional[BooleanClauseList] = None,
        params=None
    ) -> ResultProxy:
        if whereclause is None:
            pk = self._get_pk()
            whereclause = self.model.columns[pk] == instance[pk]
        query = delete(self.model, whereclause)
        return await self.execute(query, params=params)

    async def execute(
        self,
        query: Any,
        params: Any = None,
        fetch: Optional[types.Fetch] = None,
    ) -> types.ExecuteResultAioPgSA:
        if fetch is None:
            return await self._execute(query, params or {})
        if fetch == "all":
            return await self._fetchall(query, params or {})
        return await self._fetchone(query, params or {})

    async def _fetchone(self, query: str, params: dict) -> Optional[RowProxy]:
        async with self.connection.acquire() as conn:
            try:
                result: ResultProxy = await conn.execute(query, **params)
                return await result.fetchone()
            except PsycopgError as exc:
                raise self._get_exception(exc)

    async def _fetchall(self, query: str, params: dict) -> List[RowProxy]:
        async with self.connection.acquire() as conn:
            try:
                result: ResultProxy = await conn.execute(query, params)
                return await result.fetchall()
            except PsycopgError as exc:
                raise self._get_exception(exc)

    async def _execute(self, query: str, params: dict) -> ResultProxy:
        async with self.connection.acquire() as conn:
            try:
                return await conn.execute(query, params)
            except PsycopgError as exc:
                raise self._get_exception(exc)

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

    def _get_exception(self, exc: PsycopgError) -> DatabaseException:
        # NOTE(ckkz-it): https://www.postgresql.org/docs/current/errcodes-appendix.html#ERRCODES-TABLE
        if exc.pgcode in ("22P02", "42883", "23502"):
            return FieldValidationError(exc.pgerror)
        if exc.pgcode == "23503":
            return ObjectNotFound(exc.pgerror)
        if exc.pgcode == "23505":
            return UniqueViolationError(exc.pgerror)
        return DatabaseException(exc.pgerror)


class _operation:  # noqa
    @property
    def _is_aio_pg_sa(self):
        from aiohttp_rest_framework.settings import get_global_config, AIOPG_SA
        config = get_global_config()
        return config.schema_type == AIOPG_SA

    def param(self, parameter: str) -> Union[BindParameter]:
        if self._is_aio_pg_sa:
            return bindparam(parameter)
        raise NotImplementedError()

    def literal(self, value: str) -> Union[BindParameter]:
        if self._is_aio_pg_sa:
            return literal(value)
        raise NotImplementedError()

    def literal_column(self, column: str) -> Union[ColumnClause]:
        if self._is_aio_pg_sa:
            return literal_column(column)
        raise NotImplementedError()

    def and_(self, *expressions: Any) -> Union[BooleanClauseList]:
        if self._is_aio_pg_sa:
            return and_(*expressions)
        raise NotImplementedError()

    def or_(self, *expressions: Any) -> Union[BooleanClauseList]:
        if self._is_aio_pg_sa:
            return or_(*expressions)
        raise NotImplementedError()

    def not_(self, expression: Any) -> Union[BooleanClauseList]:
        if self._is_aio_pg_sa:
            return not_(expression)
        raise NotImplementedError()


operation = _operation()
op = operation
