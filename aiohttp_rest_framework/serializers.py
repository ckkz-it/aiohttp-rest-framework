import asyncio
import copy
import typing

import marshmallow as ma

from aiohttp_rest_framework.db import DatabaseServiceABC
from aiohttp_rest_framework.exceptions import ValidationError
from aiohttp_rest_framework.settings import Config, get_global_config


class empty:
    """
    This class is used to represent no data being provided for a given input
    or output value.

    It is required because `None` may be a valid input or output value.
    """
    pass


class Meta:
    pass


class SerializerOpts(ma.SchemaOpts):
    def __init__(self, meta, ordered: bool = True):
        if not hasattr(meta, "unknown"):
            meta.unknown = ma.EXCLUDE  # by default exclude unknown fields, like in drf
        super().__init__(meta, ordered)


class SerializerMeta(ma.schema.SchemaMeta):
    def __new__(mcs, name, bases, attrs):
        meta: type = attrs.get("Meta", Meta)
        meta.ordered = getattr(meta, "ordered", True)
        attrs["Meta"] = meta
        return super().__new__(mcs, name, bases, attrs)


class Serializer(ma.Schema):
    OPTIONS_CLASS = SerializerOpts
    opts: SerializerOpts = None

    instance: typing.Any = None

    def __init__(self, instance=None, data: typing.Any = empty, as_text: bool = False, **kwargs):
        self.instance = instance
        if data is not empty:
            self.initial_data = data
        self.as_text = as_text
        self._serializer_context = kwargs.pop("serializer_context", {})
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        if self.as_text:
            data = self.opts.render_module.loads(data)

        return self.load(data)

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
            list(self.validated_data.items()) + list(typing.cast(typing.Any, kwargs.items()))
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

    def is_valid(self, raise_exception=False):
        assert hasattr(self, "initial_data"), (
            "Cannot call `.is_valid()` as no `data=` keyword argument was "
            "passed when instantiating the serializer instance."
        )

        if not hasattr(self, "_validated_data"):
            try:
                self._validated_data = self.to_internal_value(self.get_initial())
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
        if self.serializer_context and "config" in self.serializer_context:
            return self.serializer_context["config"]
        return get_global_config()


class ModelSerializerOpts(SerializerOpts):
    def __init__(self, meta, ordered: bool = True):
        super().__init__(meta, ordered)
        self.model = getattr(meta, "model", None)
        self.abstract = getattr(meta, "abstract", False)


class ModelSerializerMeta(SerializerMeta):
    def __new__(mcs, name, bases, attrs):
        meta: type = attrs.get("Meta")
        is_fields_all = False
        if meta and hasattr(meta, "fields"):
            if meta.fields == "__all__":
                is_fields_all = True
                del meta.fields
                attrs["Meta"] = meta

        klass = super().__new__(mcs, name, bases, attrs)
        if not klass.opts.abstract:  # if not abstract, has to specify model
            assert klass.opts.model is not None, (
                f"{name} has to include `model` attribute in it's Meta"
            )
            if is_fields_all:
                all_fields = tuple(str(column.name) for column in klass.opts.model.columns)
                klass.opts.fields = all_fields
        return klass


class ModelSerializer(Serializer, metaclass=ModelSerializerMeta):
    OPTIONS_CLASS = ModelSerializerOpts
    opts: ModelSerializerOpts = None

    def _init_fields(self) -> None:
        super()._init_fields()
        # replace marshmallow inferred fields with database/schema specific fields
        inferred_field_builder = self.config.inferred_field_builder
        for field_name, field_obj in self.fields.items():
            if isinstance(field_obj, ma.fields.Inferred):
                inferred_field = inferred_field_builder(
                    name=field_name, serializer=self, model=self.opts.model
                ).build()
                self._bind_field(field_name, inferred_field)
                self.fields[field_name] = inferred_field
                if field_name in self.dump_fields:
                    self.dump_fields[field_name] = inferred_field
                if field_name in self.load_fields:
                    self.load_fields[field_name] = inferred_field

    async def update(self, instance: typing.Any, validated_data: typing.OrderedDict):
        db_service = await self.get_db_service()
        return await db_service.update(instance, validated_data)

    async def create(self, validated_data: typing.OrderedDict):
        db_service = await self.get_db_service()
        return await db_service.create(validated_data)

    async def get_db_service(self) -> DatabaseServiceABC:
        if asyncio.iscoroutinefunction(self.config.get_connection):
            connection = await self.config.get_connection()
        else:
            connection = self.config.get_connection()
        return self.config.db_service_class(connection, self.opts.model)

    class Meta:
        abstract = True
