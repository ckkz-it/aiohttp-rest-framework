import copy
import typing

import marshmallow as mm

from aiohttp_rest_framework.db import AioPGService, DatabaseServiceABC
from aiohttp_rest_framework.exceptions import ValidationError


class empty:
    """
    This class is used to represent no data being provided for a given input
    or output value.

    It is required because `None` may be a valid input or output value.
    """
    pass


class ModelSerializerOpts(mm.SchemaOpts):
    def __init__(self, meta, ordered: bool = False):
        super().__init__(meta, ordered)
        assert hasattr(meta, "model") and meta.model is not None, (
            "`model` option has to be specified in serializer's `Meta` class"
        )
        assert hasattr(meta, "connection") and meta.connection is not None, (
            "`connection` option has to be specified in serializer's `Meta` class"
        )
        self.ordered = True
        self.model = meta.model
        self.connection = meta.connection
        self.db_service_class: typing.Type[DatabaseServiceABC] = \
            getattr(meta, "db_service", AioPGService)


class Serializer(mm.Schema):
    instance: typing.Any = None

    def __init__(self, instance=None, data: typing.Any = empty, **kwargs):
        self.instance = instance
        if data is not empty:
            self.initial_data = data
        self.partial = kwargs.pop("partial", False)
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        return self.load(data, partial=self.partial)

    def to_representation(self, instance):
        return self.dump(instance)

    def get_initial(self):
        return copy.deepcopy(self.initial_data)

    async def update(self, instance, validated_data):
        raise NotImplementedError("`update()` must be implemented.")

    async def create(self, validated_data):
        raise NotImplementedError("`create()` must be implemented.")

    async def save(self, **kwargs):
        assert hasattr(self, "_errors"), (
            "You must call `.is_valid()` before calling `.save()`."
        )

        assert not self.errors, (
            "You cannot call `.save()` on a serializer with invalid data."
        )

        validated_data = dict(
            list(self.validated_data.items()) +
            list(typing.cast(typing.Any, kwargs.items()))
        )

        if self.instance is not None:
            self.instance = self.update(self.instance, validated_data)
            assert self.instance is not None, (
                "`update()` did not return an object instance."
            )
        else:
            self.instance = self.create(validated_data)
            assert self.instance is not None, (
                "`create()` did not return an object instance."
            )

        return self.instance

    @property
    def data(self):
        if hasattr(self, "initial_data") and not hasattr(self, "_validated_data"):
            msg = (
                "When a serializer is passed a `data` keyword argument you "
                "must call `.is_valid()` before attempting to access the "
                "serialized `.data` representation.\n"
                "You should either call `.is_valid()` first, "
                "or access `.initial_data` instead."
            )
            raise AssertionError(msg)

        if not hasattr(self, "_data"):
            if self.instance is not None and not getattr(self, "_errors", None):
                self._data = self.to_representation(self.instance)
            elif hasattr(self, "_validated_data") and not getattr(self, "_errors", None):
                self._data = self.to_representation(self.validated_data)
            else:
                self._data = self.get_initial()
        return self._data

    @property
    def errors(self):
        if not hasattr(self, "_errors"):
            msg = "You must call `.is_valid()` before accessing `.errors`."
            raise AssertionError(msg)
        return self._errors

    @property
    def validated_data(self):
        if not hasattr(self, "_validated_data"):
            msg = "You must call `.is_valid()` before accessing `.validated_data`."
            raise AssertionError(msg)
        return self._validated_data

    def is_valid(self, raise_exception=False):
        assert hasattr(self, "initial_data"), (
            "Cannot call `.is_valid()` as no `data=` keyword argument was "
            "passed when instantiating the serializer instance."
        )

        if not hasattr(self, "_validated_data"):
            try:
                self._validated_data = self.to_internal_value(self.get_initial())
            except mm.ValidationError as exc:
                self._validated_data = {}
                self._errors = exc.messages
            else:
                self._errors = {}

        if self._errors and raise_exception:
            raise ValidationError(self._errors)

        return not bool(self._errors)


class ModelSerializer(Serializer):
    _db_service: DatabaseServiceABC = None

    OPTIONS_CLASS = ModelSerializerOpts
    opts: ModelSerializerOpts = None

    async def update(self, pk: typing.Any, validated_data: typing.OrderedDict):
        return await self.db_service.update(pk, validated_data)

    async def create(self, validated_data: typing.OrderedDict):
        return await self.db_service.create(validated_data)

    @property
    def db_service(self):
        if not self._db_service:
            self._db_service = self.opts.db_service_class(self.opts.connection, self.opts.model)
        return self._db_service
