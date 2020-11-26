from aiohttp import web

from aiohttp_rest_framework.serializers import Serializer

__all__ = (
    "CreateModelMixin",
    "ListModelMixin",
    "RetrieveModelMixin",
    "UpdateModelMixin",
    "DestroyModelMixin",
)


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
        serializer = self.get_serializer(instance)
        await self.perform_destroy(serializer)
        return web.HTTPNoContent()

    async def perform_destroy(self, serializer: Serializer):
        await serializer.delete()
