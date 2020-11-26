import typing

from aiohttp import web

from aiohttp_rest_framework import APP_CONFIG_KEY
from aiohttp_rest_framework.db.base import BaseDBManager
from aiohttp_rest_framework.exceptions import HTTPNotFound, ObjectNotFound
from aiohttp_rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from aiohttp_rest_framework.serializers import Serializer
from aiohttp_rest_framework.settings import Config

__all__ = (
    "APIView",
    "GenericAPIView",
    "CreateAPIView",
    "ListAPIView",
    "RetrieveAPIView",
    "DestroyAPIView",
    "UpdateAPIView",
    "ListCreateAPIView",
    "RetrieveUpdateAPIView",
    "RetrieveDestroyAPIView",
    "RetrieveUpdateDestroyAPIView",
)


class APIView(web.View):
    """Base API View.

    Should be used when you won't use serializer and models
    for particular view.
    """

    @property
    def rest_config(self) -> Config:
        try:
            return self.request.app[APP_CONFIG_KEY]
        except KeyError:
            msg = (
                "Looks like you didn't call `setup_rest_framework(app)` "
                "function for your application."
            )
            raise AssertionError(msg)


class GenericAPIView(APIView):
    """
    A Generic API View to work with serializers and models
    """

    lookup_field: str = "id"
    lookup_url_kwarg: str = None

    serializer_class: typing.Type[Serializer] = None

    _db_manager: BaseDBManager = None

    def __init__(self, request: web.Request) -> None:
        super().__init__(request)

        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_field_value = self.request.match_info.get(lookup_url_kwarg)
        self.kwargs = {
            self.lookup_field: lookup_field_value,
        }
        self.detail = lookup_field_value is not None

    async def get_db_manager(self):
        """Get db manager applicable for current engine"""
        if not self._db_manager:
            self._db_manager = self.rest_config.db_manager_class(self.rest_config, self.model)
        return self._db_manager

    @property
    def model(self):
        serializer_class = self.get_serializer_class()
        return serializer_class.opts.model  # noqa

    def get_serializer_class(self):
        assert self.serializer_class is not None, (
            f"'{self.__class__.__name__}' should either include a `serializer_class` "
            "attribute or override `get_serializer_class()` method"
        )
        return self.serializer_class

    def get_serializer(self, *args, **kwargs) -> Serializer:
        serializer_class = self.get_serializer_class()
        kwargs.setdefault("serializer_context", self.get_serializer_context())
        return serializer_class(*args, **kwargs)

    def get_serializer_context(self):
        return {
            "request": self.request,
            "view": self,
            "config": self.rest_config,
        }

    async def get_object(self):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        params = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        db_manager = await self.get_db_manager()
        try:
            obj = await db_manager.get(params)
        except ObjectNotFound:
            raise HTTPNotFound()
        return obj

    async def get_list(self):
        db_manager = await self.get_db_manager()
        return await db_manager.all()


class CreateAPIView(CreateModelMixin,
                    GenericAPIView):
    async def post(self):
        return await self.create()


class ListAPIView(ListModelMixin,
                  GenericAPIView):
    async def get(self):
        return await self.list()


class RetrieveAPIView(RetrieveModelMixin,
                      GenericAPIView):
    async def get(self):
        return await self.retrieve()


class DestroyAPIView(DestroyModelMixin,
                     GenericAPIView):
    async def delete(self):
        return await self.destroy()


class UpdateAPIView(UpdateModelMixin,
                    GenericAPIView):
    async def put(self):
        return await self.update()

    async def patch(self):
        return await self.partial_update()


class ListCreateAPIView(ListModelMixin,
                        CreateModelMixin,
                        GenericAPIView):
    async def get(self):
        return await self.list()

    async def post(self):
        return await self.create()


class RetrieveUpdateAPIView(RetrieveModelMixin,
                            UpdateModelMixin,
                            GenericAPIView):
    async def get(self):
        return await self.retrieve()

    async def put(self):
        return await self.update()

    async def patch(self):
        return await self.partial_update()


class RetrieveDestroyAPIView(RetrieveModelMixin,
                             DestroyModelMixin,
                             GenericAPIView):
    async def get(self):
        return await self.retrieve()

    async def delete(self):
        return await self.destroy()


class RetrieveUpdateDestroyAPIView(RetrieveModelMixin,
                                   UpdateModelMixin,
                                   DestroyModelMixin,
                                   GenericAPIView):
    async def get(self):
        return await self.retrieve()

    async def put(self):
        return await self.update()

    async def patch(self):
        return await self.partial_update()

    async def delete(self):
        return await self.destroy()
