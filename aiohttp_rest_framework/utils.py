import inspect
import typing

import sqlalchemy as sa

__all__ = (
    "C1",
    "C2",
    "ClassLookupDict",
    "get_model_fields_sa",
    "safe_issubclass",
)

C1 = typing.TypeVar("C1")
C2 = typing.TypeVar("C2")


class ClassLookupDict(typing.Generic[C1, C2]):
    """
    Takes a dictionary with classes as keys.
    Lookups against this object will traverses the object's inheritance
    hierarchy in method resolution order, and returns the first matching value
    from the dictionary.
    """

    def __init__(self, mapping: typing.Dict[C1, C2]):
        self.mapping = mapping

    def __getitem__(self, key) -> C2:
        base_class = key.__class__
        for cls in inspect.getmro(base_class):
            if cls in self.mapping:
                return self.mapping[cls]
        raise KeyError(f"Class {key.__name__} not found in lookup.")

    def __setitem__(self, key, value) -> None:
        self.mapping[key] = value

    def get(self, key: C1, default=None) -> typing.Optional[C2]:
        try:
            return self.__getitem__(key)
        except KeyError:
            return default

    def __reversed__(self):
        return self.__class__({value: key for key, value in self.mapping.items()})

    def __contains__(self, item) -> bool:
        try:
            self.__getitem__(item)
            return True
        except KeyError:
            return False


def get_model_fields_sa(model: sa.Table) -> typing.Tuple[str]:
    return tuple(str(column.name) for column in model.columns)


def safe_issubclass(first, other):
    try:
        return issubclass(first, other)
    except TypeError:
        return False
