import typing

from aiopg.sa.result import ResultProxy, RowProxy

ExecuteResultAioPg = typing.Union[typing.List[RowProxy], typing.Optional[RowProxy], ResultProxy]

Fetch = typing.Literal["one", "all"]
