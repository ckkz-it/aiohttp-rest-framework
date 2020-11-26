from typing import Generic, List, TypeVar

T = TypeVar("T")


class BaseDBManager(Generic[T]):
    async def get(self, *args, **kwargs) -> T:
        raise NotImplementedError()

    async def all(self, *args, **kwargs) -> List[T]:
        raise NotImplementedError()

    async def filter(self, *args, **kwargs) -> List[T]:
        raise NotImplementedError()

    async def create(self, *args, **kwargs) -> T:
        raise NotImplementedError()

    async def update(self, *args, **kwargs) -> T:
        raise NotImplementedError()

    async def delete(self, *args, **kwargs) -> None:
        raise NotImplementedError()
