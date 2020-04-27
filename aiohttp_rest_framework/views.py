import typing

from aiohttp import web
from aiohttp_cors import CorsViewMixin

from aiohttp_rest_framework.db import DatabaseServiceABC
from aiohttp_rest_framework.serializers import Serializer
from aiohttp_rest_framework.settings import APP_CONFIG_KEY, Config


class GenericAPIView(CorsViewMixin, web.View):
    lookup_field = "id"
    lookup_url_kwarg = None

    serializer_class: typing.Type[Serializer] = None

    _db_service: DatabaseServiceABC = None

    def __init__(self, request: web.Request) -> None:
        super().__init__(request)

        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_field_value = self.request.match_info.get(lookup_url_kwarg)
        self.kwargs = {
            self.lookup_field: lookup_field_value,
        }
        self.detail = lookup_field_value is not None

    @property
    def db_service(self):
        if not self._db_service:
            self._db_service = \
                self.rest_config.db_service_class(self.rest_config.get_connection(), self.model)
        return self._db_service

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
        kwargs["serializer_context"] = self.get_serializer_context()
        return serializer_class(*args, **kwargs)

    def get_serializer_context(self):
        return {
            "request": self.request,
            "view": self,
            "config": self.rest_config,
        }

    @property
    def rest_config(self) -> Config:
        try:
            return self.request.app[APP_CONFIG_KEY]
        except KeyError:
            msg = (
                "Looks like you didn't call `setup_rest_framework()` "
                "function for your application."
            )
            raise AssertionError(msg)

    async def get_object(self):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        where = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        obj = await self.db_service.get(where)  # may raise `ObjectNotFound` exception
        return obj

    async def get_list(self):
        return await self.db_service.filter()


class CreateModelMixin:
    async def create(self):
        data = await self.request.text()
        serializer = self.get_serializer(data=data, as_text=True)
        serializer.is_valid(raise_exception=True)

        await self.perform_create(serializer)
        return web.json_response(serializer.data, status=201)

    async def perform_create(self, serializer: Serializer):
        return await serializer.save()


class ListModelMixin:
    async def list(self):
        instances = await self.get_list()
        serializer = self.get_serializer(instances, many=True)
        return web.json_response(serializer.data)


class RetrieveModelMixin:
    async def retrieve(self):
        instance = await self.get_object()
        serializer = self.get_serializer(instance)
        return web.json_response(serializer.data)


class UpdateModelMixin:
    async def update(self):
        instance = await self.get_object()

        data = await self.request.text()
        partial = self.kwargs.pop("partial", False)
        serializer = self.get_serializer(instance, data=data, as_text=True,
                                         partial=partial)
        serializer.is_valid(raise_exception=True)

        await self.perform_update(serializer)

        return web.json_response(serializer.data)

    def partial_update(self):
        self.kwargs["partial"] = True
        return self.update()

    async def perform_update(self, serializer: Serializer):
        return await serializer.save()


class DestroyModelMixin:
    async def destroy(self):
        instance = await self.get_object()
        await self.perform_destroy(instance)
        return web.HTTPNoContent()

    async def perform_destroy(self, instance):
        await self.db_service.delete(instance)


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
