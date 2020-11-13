from typing import Any, Union

from sqlalchemy import bindparam
from sqlalchemy.sql.elements import (
    BindParameter,
    BooleanClauseList,
    ColumnClause,
    and_,
    literal,
    literal_column,
    not_,
    or_,
)


class _operation:  # noqa
    @property
    def _is_sqlalchemy(self):
        from aiohttp_rest_framework.settings import get_global_config
        config = get_global_config()
        return "_sa" in config.schema_type

    def param(self, parameter: str) -> Union[BindParameter]:
        if self._is_sqlalchemy:
            return bindparam(parameter)
        raise NotImplementedError()

    def literal(self, value: str) -> Union[BindParameter]:
        if self._is_sqlalchemy:
            return literal(value)
        raise NotImplementedError()

    def literal_column(self, column: str) -> Union[ColumnClause]:
        if self._is_sqlalchemy:
            return literal_column(column)
        raise NotImplementedError()

    def and_(self, *expressions: Any) -> Union[BooleanClauseList]:
        if self._is_sqlalchemy:
            return and_(*expressions)
        raise NotImplementedError()

    def or_(self, *expressions: Any) -> Union[BooleanClauseList]:
        if self._is_sqlalchemy:
            return or_(*expressions)
        raise NotImplementedError()

    def not_(self, expression: Any) -> Union[BooleanClauseList]:
        if self._is_sqlalchemy:
            return not_(expression)
        raise NotImplementedError()


operation = _operation()
op = operation
