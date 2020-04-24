import inspect
import typing


class ClassLookupDict:
    """
    Takes a dictionary with classes as keys.
    Lookups against this object will traverses the object's inheritance
    hierarchy in method resolution order, and returns the first matching value
    from the dictionary.
    """

    def __init__(self, mapping: typing.Dict[type, type]):
        self.mapping = mapping

    def __getitem__(self, key) -> type:
        base_class = key.__class__
        for cls in inspect.getmro(base_class):
            if cls in self.mapping:
                return self.mapping[cls]
        raise KeyError(f"Class {key.__name__} not found in lookup.")

    def __setitem__(self, key, value) -> None:
        self.mapping[key] = value

    def get(self, key, default=None) -> typing.Optional[type]:
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
