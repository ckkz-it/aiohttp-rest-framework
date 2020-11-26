from typing import Any, Dict, List, Mapping, Optional, Union

from asyncpg import (
    ForeignKeyViolationError,
    InvalidTextRepresentationError,
    NotNullViolationError,
    PostgresError,
    UndefinedFunctionError,
)
from psycopg2._psycopg import Error as PsycopgError
from psycopg2.errorcodes import (
    FOREIGN_KEY_VIOLATION,
    INVALID_TEXT_REPRESENTATION,
    NOT_NULL_VIOLATION,
    UNDEFINED_FUNCTION,
    UNIQUE_VIOLATION,
)
from sqlalchemy import Column, Table, and_, delete, insert, update
from sqlalchemy.engine import Row
from sqlalchemy.exc import (
    DBAPIError,
    IntegrityError,
    MultipleResultsFound,
    NoResultFound,
    ProgrammingError,
    SQLAlchemyError,
    StatementError,
)
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import Executable
from sqlalchemy.sql.elements import BooleanClauseList, literal_column

from aiohttp_rest_framework.db.base import BaseDBManager
from aiohttp_rest_framework.exceptions import (
    FieldValidationError,
    MultipleObjectsReturned,
    ObjectNotFound,
    UniqueViolationError,
)


class SAManager(BaseDBManager):
    def __init__(self, config, model) -> None:
        from aiohttp_rest_framework.settings import Config
        self.model = model
        self.config: Config = config
        self._engine = None
        self._is_core = isinstance(self.model, Table)

    async def get(self, filter_params: Optional[Dict] = None, whereclause: Optional[BooleanClauseList] = None):
        query = select(self.model)
        if whereclause is not None:
            query = query.where(whereclause)
        else:
            query = query.where(self._construct_whereclause(filter_params))

        try:
            return await self.execute(query, operation="one")
        except FieldValidationError as exc:
            raise ObjectNotFound(str(exc))

    async def all(self) -> List[Any]:
        query = select(self.model)
        return await self.execute(query, operation="all")

    async def filter(
        self,
        filter_params: Optional[Dict] = None,
        whereclause: Optional[BooleanClauseList] = None,
    ) -> List[Any]:
        query = select(self.model)
        if whereclause is not None:
            query = query.where(whereclause)
        else:
            query = query.where(self._construct_whereclause(filter_params))

        return await self.execute(query, operation="all")

    async def create(self, values: Mapping) -> Any:
        query = insert(self.model).values(values).returning(literal_column("*"))
        result = await self.execute(query, operation="one", no_scalars=True)
        return self.to_model_instance(result)

    async def update(self, instance, values: Mapping):
        query = update(
            self.model
        ).where(
            self.get_pk_column() == getattr(instance, self.pk)
        ).values(values).returning(literal_column("*"))

        try:
            result = await self.execute(query, operation="one", no_scalars=True)
            return self.to_model_instance(result)
        except (NoResultFound, FieldValidationError) as exc:
            raise ObjectNotFound(str(exc))
        except MultipleResultsFound as exc:
            raise MultipleObjectsReturned(str(exc))

    async def delete(self, instance) -> None:
        query = delete(self.model).where(self.get_pk_column() == getattr(instance, self.pk))
        await self.execute(query)

    async def execute(
        self,
        query: Executable,
        parameters: Optional[Mapping] = None,
        operation: Optional[str] = None,
        no_scalars: bool = False,
    ) -> Any:
        engine = await self.get_engine()
        async with AsyncSession(engine, expire_on_commit=False) as session:
            async with session.begin():
                try:
                    result = await session.execute(query, parameters)
                    if operation:
                        if not no_scalars and not self._is_core:
                            result = result.scalars()
                        result = getattr(result, operation)()
                except (SQLAlchemyError, PostgresError) as exc:
                    raise self._get_exception(exc)
            await session.commit()
            return result

    async def get_engine(self) -> AsyncEngine:
        return await self.config.get_connection()

    @property
    def pk(self) -> Any:
        if self._is_core:
            pks = self.model.primary_key.columns.keys()
        else:
            pks = self.model.__table__.primary_key.columns.keys()
        return pks[0]

    def get_pk_column(self) -> Column:
        if self._is_core:
            return self.model.columns[self.pk]
        return getattr(self.model, self.pk)

    def _construct_whereclause(self, params: Dict) -> BooleanClauseList:
        if self._is_core:
            return and_(self.model.columns[key] == value for key, value in params.items())
        return and_(getattr(self.model, key) == value for key, value in params.items())

    def _get_exception(self, exc: Union[SQLAlchemyError, PostgresError]) -> Exception:
        if isinstance(exc, StatementError):
            if isinstance(exc.orig, PsycopgError):
                if exc.orig.pgcode in (INVALID_TEXT_REPRESENTATION, UNDEFINED_FUNCTION, NOT_NULL_VIOLATION):
                    return FieldValidationError(exc.orig.pgerror)
                if exc.orig.pgcode == FOREIGN_KEY_VIOLATION:
                    return ObjectNotFound(exc.orig.pgerror)
                if exc.orig.pgcode == UNIQUE_VIOLATION:
                    return UniqueViolationError(exc.orig.pgerror)

            if isinstance(exc, IntegrityError):
                if NotNullViolationError.__name__ in exc.args[0]:
                    return FieldValidationError(str(exc))
                if ForeignKeyViolationError.__name__ in exc.args[0]:
                    return FieldValidationError(str(exc))

            if isinstance(exc, ProgrammingError):
                if UndefinedFunctionError.__name__ in exc.args[0]:
                    return FieldValidationError(str(exc))

            if type(exc) is StatementError:
                return FieldValidationError(str(exc))

        if isinstance(exc, DBAPIError):
            if InvalidTextRepresentationError.__name__ in exc.args[0]:
                return FieldValidationError(str(exc))

        if isinstance(exc, NoResultFound):
            return ObjectNotFound(str(exc))
        if isinstance(exc, MultipleResultsFound):
            return MultipleObjectsReturned(str(exc))

        return exc

    def to_model_instance(self, result: Row) -> Any:
        if self._is_core:
            return result
        return self.model(**result._asdict())
