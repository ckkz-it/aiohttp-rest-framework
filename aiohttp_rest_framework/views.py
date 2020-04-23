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

        method = self.request.method.lower()
        if method in ["put", "patch"]:
            self.kwargs["partial"] = method == "patch"

    @property
    def db_service(self):
        if not self._db_service:
            self._db_service = \
                self.rest_config.db_service_class(self.rest_config.get_connection(), self.model)
        return self._db_service

    @property
    def model(self):
        serializer_class = self.get_serializer_class()
        assert serializer_class.Meta.model is not None, (
            f"`model` attribute for {serializer_class.__class__.__name__}'s `Meta` has to be set"
        )
        return self.get_serializer_class().Meta.model

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
        obj = await self.db_service.get(where)
        if not obj:
            raise web.HTTPNotFound()
        return obj

    async def get_list(self):
        return await self.db_service.filter(None)


class CreateModelMixin:
    async def create(self, *args, **kwargs):
        data = await self.request.text()
        serializer = self.get_serializer(data=data, as_text=True)
        serializer.is_valid(raise_exception=True)

        await self.perform_create(serializer)
        # instance = await self.get_object()
        return web.json_response(serializer.data, status=201)

    async def perform_create(self, serializer: Serializer):
        return await serializer.save()


class ListModelMixin:
    async def list(self, *args, **kwargs):
        instances = await self.get_list()
        serializer = self.get_serializer(instances, many=True)
        return web.json_response(serializer.data)


class RetrieveModelMixin:
    async def retrieve(self, *args, **kwargs):
        instance = await self.get_object()
        serializer = self.get_serializer(instance)
        return web.json_response(serializer.data)


class UpdateModelMixin:
    async def update(self, *args, **kwargs):
        instance = await self.get_object()  # may raise 404

        data = await self.request.text()
        serializer = self.get_serializer(instance, data=data, as_text=True,
                                         partial=self.kwargs["partial"])
        serializer.is_valid(raise_exception=True)

        await self.perform_update(serializer)

        return web.json_response(serializer.data)

    def partial_update(self, *args, **kwargs):
        return self.update(*args, **kwargs)

    async def perform_update(self, serializer: Serializer):
        return await serializer.save()


class DestroyModelMixin:
    async def destroy(self, *args, **kwargs):
        pass

    async def perform_destroy(self, instance):
        pass


class CreateAPIView(CreateModelMixin,
                    GenericAPIView):
    async def post(self, *args, **kwargs):
        return await self.create(*args, **kwargs)


class ListAPIView(ListModelMixin,
                  GenericAPIView):
    async def get(self, *args, **kwargs):
        return await self.list(*args, **kwargs)


class RetrieveAPIView(RetrieveModelMixin,
                      GenericAPIView):
    async def get(self, *args, **kwargs):
        return await self.retrieve(*args, **kwargs)


class DestroyAPIView(DestroyModelMixin,
                     GenericAPIView):
    async def delete(self, *args, **kwargs):
        return await self.destroy(*args, **kwargs)


class UpdateAPIView(UpdateModelMixin,
                    GenericAPIView):
    async def put(self, *args, **kwargs):
        return await self.update(*args, **kwargs)

    async def patch(self, *args, **kwargs):
        return await self.partial_update(*args, **kwargs)


class ListCreateAPIView(ListModelMixin,
                        CreateModelMixin,
                        GenericAPIView):
    async def get(self, *args, **kwargs):
        return await self.list(*args, **kwargs)

    async def post(self, *args, **kwargs):
        return await self.create(*args, **kwargs)


class RetrieveUpdateAPIView(RetrieveModelMixin,
                            UpdateModelMixin,
                            GenericAPIView):
    async def get(self, *args, **kwargs):
        return await self.retrieve(*args, **kwargs)

    async def put(self, *args, **kwargs):
        return await self.update(*args, **kwargs)

    async def patch(self, *args, **kwargs):
        return await self.partial_update(*args, **kwargs)


class RetrieveDestroyAPIView(RetrieveModelMixin,
                             DestroyModelMixin,
                             GenericAPIView):
    async def get(self, *args, **kwargs):
        return await self.retrieve(*args, **kwargs)

    async def delete(self, *args, **kwargs):
        return await self.destroy(*args, **kwargs)


class RetrieveUpdateDestroyAPIView(RetrieveModelMixin,
                                   UpdateModelMixin,
                                   DestroyModelMixin,
                                   GenericAPIView):
    async def get(self, *args, **kwargs):
        return await self.retrieve(*args, **kwargs)

    async def put(self, *args, **kwargs):
        return await self.update(*args, **kwargs)

    async def patch(self, *args, **kwargs):
        return await self.partial_update(*args, **kwargs)

    async def delete(self, *args, **kwargs):
        return await self.destroy(*args, **kwargs)
