from typing import Any, Generic, List, Optional, TypeVar

from databases import Database
from sqlalchemy import Table
from sqlalchemy.sql.elements import BooleanClauseList
from sqlalchemy.sql.expression import ColumnElement, Delete, Insert, Select, Update, delete, insert, select, update

from aiohttp_rest_framework.exceptions import ObjectNotFound

T = TypeVar("T")  # pylint: disable=invalid-name


class CommonQueryBuilderMixin:
    @property
    def table(self) -> Table:
        raise NotImplementedError()

    @property
    def pk_key(self) -> str:
        """
        Take first primary key even if there are many,
        it doesn't matter when we just need to get object for update/delete
        """
        pks = self.table.primary_key.columns.keys()
        return pks[0]

    @property
    def pk_column(self) -> ColumnElement:
        return self.table.columns[self.pk_key]

    def get_by_id_query(self, id_: Any) -> Select:
        return self.get_all_query().where(self.pk_column == id_)

    def delete_by_id_query(self, id_: Any) -> Delete:
        return delete(self.table).where(self.pk_column == id_)

    def get_all_query(self) -> Select:
        return select([self.table])

    def insert_query(self, values, with_returning: bool = False) -> Insert:
        query = insert(self.table, values)
        if with_returning:
            # TODO(ckkz-it): fix bug for databases library with `literal_column("*")`
            query = query.returning(*self.table.columns)
        return query

    def update_query(self, whereclause: Optional[BooleanClauseList] = None, with_returning: bool = False) -> Update:
        query = update(self.table, whereclause)
        if with_returning:
            query = query.returning(*self.table.columns)
        return query

    def delete_query(self, whereclause: Optional[BooleanClauseList] = None) -> Delete:
        query = delete(self.table, whereclause)
        return query

    def delete_all_query(self) -> Delete:
        return delete(self.table)


class BaseSARepository(Generic[T], CommonQueryBuilderMixin):
    not_found_exception_cls = ObjectNotFound

    def __init__(self, table: Table, connection: Optional[Database] = None):
        from aiohttp_rest_framework.settings import get_global_config
        self._config = get_global_config()
        self._table = table
        self._connection = connection

    @property
    def table(self) -> Table:
        return self._table

    async def _fetchone(self, *args, **kwargs) -> Optional[T]:
        raise NotImplementedError()

    async def _fetchall(self, *args, **kwargs) -> List[T]:
        raise NotImplementedError()

    async def _execute(self, *args, **kwargs):
        raise NotImplementedError()

    async def get_connection(self) -> Database:
        if self._connection:
            return self._connection
        self._connection = await self._config.get_connection()
        return self._connection
