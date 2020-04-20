import typing

from aiopg.sa.result import RowProxy, ResultProxy

ExecuteResultAioPg = typing.Union[typing.List[RowProxy], typing.Optional[RowProxy], ResultProxy]

Fetch = typing.Literal['one', 'all']
