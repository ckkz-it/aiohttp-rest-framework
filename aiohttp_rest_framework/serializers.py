import copy
from itertools import chain
from json import JSONDecodeError
from typing import Any, Generic, Optional, OrderedDict, Sequence, TypeVar, cast, Mapping

import marshmallow as ma

from aiohttp_rest_framework.db.base import BaseDBManager
from aiohttp_rest_framework.exceptions import DatabaseException, ValidationError
from aiohttp_rest_framework.settings import Config, get_global_config

__all__ = (
    "empty",
    "Meta",
    "SerializerOpts",
    "SerializerMeta",
    "Serializer",
    "ModelSerializerOpts",
    "ModelSerializerMeta",
    "ModelSerializer",
)


class empty:
    """
    This class is used to represent no data being provided for a given input
    or output value.

    It is required because `None` may be a valid input or output value.
    """


class Meta:
    """Use as default when `Meta` is not provided is serializer"""


class SerializerOpts(ma.SchemaOpts):
    def __init__(self, meta, ordered: bool = True):
        if not hasattr(meta, "unknown"):
            meta.unknown = ma.EXCLUDE  # by default exclude unknown fields, like in drf
        super().__init__(meta, ordered)


class SerializerMeta(ma.schema.SchemaMeta):
    def __new__(mcs, name, bases, attrs):
        meta = mcs.get_meta(bases, attrs)
        meta.ordered = getattr(meta, "ordered", True)
        attrs["Meta"] = meta
        return super().__new__(mcs, name, bases, attrs)

    @classmethod
    def get_meta(mcs, bases, attrs):
        meta: type = attrs.get("Meta")
        if meta:
            return meta
        # inherit Meta from first base class with Meta declared
        for base_ in bases:
            if hasattr(base_, "Meta"):
                return base_.Meta
        # otherwise use empty Meta
        return Meta


T = TypeVar("T")


class Serializer(Generic[T], ma.Schema):
    _config: Config = None

    OPTIONS_CLASS = SerializerOpts
    opts: SerializerOpts = None

    instance: Any = None

    def __init__(self, instance: Optional[T] = None, data: Any = empty, as_text: bool = False, **kwargs):
        self.instance = instance
        if data is not empty:
            self.initial_data = data
        self.as_text = as_text
        self._serializer_context = kwargs.pop("serializer_context", {})
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        try:
            if self.as_text:
                return self.loads(data)
            return self.load(data)
        except JSONDecodeError:
            raise ValidationError({"error": "invalid json"})

    def to_representation(self, instance: T):
        return self.dump(instance)

    def get_initial(self):
        return copy.deepcopy(self.initial_data)

    async def delete(self) -> None:
        raise NotImplementedError("`update()` must be implemented.")

    async def update(self, instance: T, validated_data) -> T:
        raise NotImplementedError("`update()` must be implemented.")

    async def create(self, validated_data) -> T:
        raise NotImplementedError("`create()` must be implemented.")

    async def save(self, **kwargs) -> T:
        assert hasattr(self, "_errors"), (
            "You must call `.is_valid()` before calling `.save()`."
        )

        assert not self.errors, (
            "You cannot call `.save()` on a serializer with invalid data."
        )

        validated_data = dict(
            list(self.validated_data.items()) + list(cast(Any, kwargs.items()))
        )

        if self.instance is not None:
            self.instance = await self.update(self.instance, validated_data)
            assert self.instance is not None, (
                "`update()` did not return an object instance."
            )
        else:
            self.instance = await self.create(validated_data)
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

    def is_valid(self, raise_exception=False) -> bool:
        assert hasattr(self, "initial_data"), (
            "Cannot call `.is_valid()` as no `data=` keyword argument was "
            "passed when instantiating the serializer instance."
        )

        initial_data = self.get_initial()
        if not initial_data:
            raise ValidationError({"error": "No data provided"})

        if not hasattr(self, "_validated_data"):
            try:
                self._validated_data = self.to_internal_value(initial_data)
            except ma.ValidationError as exc:
                self._validated_data = {}
                self._errors = exc.messages
            else:
                self._errors = {}

        if self._errors and raise_exception:
            raise ValidationError(self._errors)

        return not bool(self._errors)

    @property
    def serializer_context(self):
        return self._serializer_context

    @property
    def config(self) -> Config:
        if not self._config:
            if self.serializer_context and "config" in self.serializer_context:
                self._config = self.serializer_context["config"]
            else:
                self._config = get_global_config()
        return self._config


class ModelSerializerOpts(SerializerOpts):
    def __init__(self, meta, ordered: bool = True):
        super().__init__(meta, ordered)
        self.model = getattr(meta, "model", None)
        self.abstract = getattr(meta, "abstract", False)


class ModelSerializerMeta(SerializerMeta):
    def __new__(mcs, name, bases, attrs):
        meta: type = mcs.get_meta(bases, attrs)
        is_fields_all = mcs.get_is_fields_all(meta, bases, attrs)

        klass = super().__new__(mcs, name, bases, attrs)
        if not klass.opts.abstract:  # if not abstract, has to specify model
            assert klass.opts.model is not None, (
                f"{name} has to include `model` attribute in it's Meta"
            )
            klass._is_fields_all = is_fields_all
        return klass

    @classmethod
    def get_is_fields_all(mcs, meta, bases, attrs) -> bool:
        if hasattr(meta, "fields"):
            if meta.fields == "__all__":
                del meta.fields
                attrs["Meta"] = meta
                return True
            return False

        for base_ in bases:  # check if it's set in base classes
            if hasattr(base_, "_is_fields_all"):
                return True
        return False


class ModelSerializer(Serializer[T], metaclass=ModelSerializerMeta):
    OPTIONS_CLASS = ModelSerializerOpts
    opts: ModelSerializerOpts = None

    def _init_fields(self) -> None:
        if self._is_fields_all:  # is set in meta class
            # add model fields to declared on serializer fields
            combined_fields = chain(self._get_model_field_names(), self.declared_fields.keys())
            self.opts.fields = self.set_class(combined_fields)
        super()._init_fields()
        # replace marshmallow inferred fields with database/schema specific fields
        field_builder = self.config.field_builder()
        for field_name, field_obj in self.fields.items():
            if isinstance(field_obj, ma.fields.Inferred):
                new_field = field_builder.build(
                    name=field_name, serializer=self, model=self.opts.model
                )
                self._bind_field(field_name, new_field)
                self.fields[field_name] = new_field

                if field_name in self.dump_fields:
                    self.dump_fields[field_name] = new_field
                if field_name in self.load_fields:
                    self.load_fields[field_name] = new_field

    def _get_model_field_names(self) -> Sequence[str]:
        """
        Override this method for custom logic getting model fields when __all__ specified
        By default it's specified in config for concrete db/orm mapping
        """
        return self.config.get_model_fields(self.opts.model)

    async def update(self, instance: T, validated_data: Mapping) -> T:
        db_service = await self.get_db_manager()
        try:
            return await db_service.update(instance, validated_data)
        except DatabaseException as e:
            raise ValidationError({"error": e.message})

    async def create(self, validated_data: Mapping) -> T:
        db_service = await self.get_db_manager()
        try:
            return await db_service.create(validated_data)
        except DatabaseException as e:
            raise ValidationError({"error": e.message})

    async def delete(self, instance: Optional[T] = None) -> None:
        assert self.instance or instance, "instance has to be defined to delete object"
        instance = self.instance or instance
        db_service = await self.get_db_manager()
        try:
            return await db_service.delete(instance)
        except DatabaseException as e:
            raise ValidationError({"error": e.message})

    async def get_db_manager(self) -> BaseDBManager:
        return self.config.db_manager_class(self.config, self.opts.model)

    class Meta:
        abstract = True
