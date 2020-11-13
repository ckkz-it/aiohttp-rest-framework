from typing import Any, List, Mapping, MutableMapping, Optional, Union

from asyncpg import exceptions
from databases import Database
from sqlalchemy import Table, and_, func, select
from sqlalchemy.sql import Select
from sqlalchemy.sql.elements import BooleanClauseList

from aiohttp_rest_framework.db.base_sa import BaseSARepository
from aiohttp_rest_framework.exceptions import (
    DatabaseException,
    FieldValidationError,
    ObjectNotFound,
    UniqueViolationError,
)

__all__ = [
    "PGSAService",
    "PGSARepository",
]


class PGSARepository(BaseSARepository[Mapping]):
    async def _fetchone(self, query: str, params: Optional[dict] = None) -> Optional[Mapping]:
        connection = await self.get_connection()
        try:
            return await connection.fetch_one(query, params)
        except exceptions.PostgresError as exc:
            raise self._get_exception(exc)

    async def _fetchall(self, query: str, params: Optional[dict] = None) -> List[Mapping]:
        connection = await self.get_connection()
        try:
            return await connection.fetch_all(query, params)
        except exceptions.PostgresError as exc:
            raise self._get_exception(exc)

    async def _execute(self, query: str, params: Optional[dict] = None) -> Any:
        connection = await self.get_connection()
        try:
            return await connection.execute(query, params)
        except exceptions.PostgresError as exc:
            raise self._get_exception(exc)

    async def get_by_id(self, instance_id: Any) -> Optional[Mapping]:
        query = self.get_by_id_query(instance_id)
        return await self._fetchone(query)

    async def get_or_raise_by_id(self, instance_id: Any) -> Mapping:
        result = await self.get_by_id(instance_id)
        if result is None:
            raise self.not_found_exception_cls()
        return result

    async def get_all(self) -> List[Mapping]:
        query = self.get_all_query()
        return await self._fetchall(query, {})

    async def update(
        self,
        instance: Union[Mapping, MutableMapping],
        params: dict,
        filter_params: Optional[MutableMapping] = None,
        whereclause: Optional[BooleanClauseList] = None,
        with_returning: bool = True,
    ) -> Optional[Mapping]:
        if not filter_params:
            filter_params = {self.pk_key: instance[self.pk_key]}

        whereclause = whereclause or self._construct_whereclause(filter_params)

        query = self.update_query(whereclause, with_returning)

        if with_returning:
            return await self._fetchone(query, params)

        result = await self._execute(query, params)
        return result

    async def delete(
        self,
        instance: MutableMapping,
        filter_params: Optional[MutableMapping] = None,
        whereclause: Optional[BooleanClauseList] = None,
    ) -> None:
        if not whereclause:
            if filter_params:
                if instance:
                    filter_params[self.pk_key] = instance[self.pk_key]
            else:
                filter_params = {self.pk_key: instance[self.pk_key]}

            whereclause = self._construct_whereclause(filter_params)

        query = self.delete_query(whereclause)

        await self._execute(query)

    async def insert(self, params: MutableMapping, with_returning: bool = True) -> Union[int, Mapping]:
        query = self.insert_query(params, with_returning)
        if with_returning:
            res = await self._fetchone(query)
            return res

        result = await self._execute(query)
        return result

    async def delete_all(self):
        query = self.delete_all_query()
        return await self._execute(query)

    async def delete_by_id(self, instance_id) -> None:
        query = self.delete_by_id_query(instance_id)
        result = await self._execute(query)
        if result == 0:
            raise self.not_found_exception_cls()

    def get_all_count_query(self) -> Select:
        return select([func.count(self.pk_column).label("count")])

    async def get_all_count(self) -> int:
        query = self.get_all_count_query()
        result = await self._fetchone(query)
        return int(result["count"])

    async def get(
        self,
        params: Optional[MutableMapping] = None,
        whereclause: Optional[BooleanClauseList] = None,
    ) -> Mapping:
        query = select([self.table])
        if whereclause is not None:
            query = query.where(whereclause)
            return await self._fetchone(query)

        query = query.where(self._construct_whereclause(params))
        result = await self._fetchone(query)
        if result is None:
            raise ObjectNotFound()
        return result

    async def filter(
        self,
        params: Optional[MutableMapping] = None,
        whereclause: Optional[BooleanClauseList] = None,
    ) -> List[Mapping]:
        query = select([self.table])
        if whereclause:
            query = query.where(whereclause)
            return await self._fetchall(query)

        query = query.where(self._construct_whereclause(params))
        return await self._fetchall(query)

    def _construct_whereclause(self, params: MutableMapping) -> BooleanClauseList:
        return and_(self.table.columns[key] == value for key, value in params.items())

    def _get_exception(self, exc: exceptions.PostgresError) -> DatabaseException:
        if isinstance(exc, (
            exceptions.InvalidTextRepresentationError,
            exceptions.UndefinedFunctionError,
            exceptions.NotNullViolationError,
            exceptions.DataError,
        )):
            return FieldValidationError(str(exc))
        if isinstance(exc, exceptions.ForeignKeyViolationError):
            return ObjectNotFound(str(exc))
        if isinstance(exc, exceptions.UniqueViolationError):
            return UniqueViolationError(str(exc))
        return DatabaseException(str(exc))


class PGSAService:
    def __init__(self, model: Table, connection: Optional[Database] = None):
        self.model = model
        self.connection = connection
        self.repo = PGSARepository(model, connection)

    async def get_by_id(self, instance_id: Any) -> Optional[Mapping]:
        return await self.repo.get_by_id(instance_id)

    async def get_or_raise_by_id(self, instance_id: Any) -> Mapping:
        return await self.repo.get_or_raise_by_id(instance_id)

    async def get(
        self,
        params: Optional[MutableMapping] = None,
        whereclause: Optional[BooleanClauseList] = None,
    ) -> Mapping:
        try:
            return await self.repo.get(params, whereclause)
        except FieldValidationError:
            raise ObjectNotFound()

    async def all(self) -> List[Mapping]:
        return await self.repo.get_all()

    async def filter(
        self,
        filter_params: Optional[MutableMapping] = None,
        whereclause: Optional[BooleanClauseList] = None,
    ) -> List[Mapping]:
        return await self.repo.filter(filter_params, whereclause)

    async def create(self, params: MutableMapping, with_returning: bool = True) -> Mapping:
        return await self.repo.insert(params, with_returning=with_returning)

    async def update(
        self,
        instance: Union[Mapping, MutableMapping],
        params: dict,
        filter_params: Optional[MutableMapping] = None,
        whereclause: Optional[BooleanClauseList] = None,
        with_returning: bool = True,
    ) -> Mapping:
        return await self.repo.update(
            instance,
            params,
            filter_params,
            whereclause,
            with_returning,
        )

    async def delete(
        self,
        instance: MutableMapping,
        filter_params: Optional[MutableMapping] = None,
        whereclause: Optional[BooleanClauseList] = None,
    ) -> int:
        try:
            return await self.repo.delete(instance, filter_params, whereclause)
        except FieldValidationError:
            raise ObjectNotFound()
