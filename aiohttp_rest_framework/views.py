import typing

from aiohttp import web

from aiopg.sa import Engine

from aiohttp_cors import CorsViewMixin

import sqlalchemy as sa

from marshmallow import Schema, ValidationError


class GenericAPIView(CorsViewMixin, web.View):
    lookup_field = 'id'
    lookup_url_kwarg = None

    query = None
    page_size = None

    db_table: sa.Table = None
    schema_class: typing.Type[Schema] = None
    validation_schema_class: typing.Type[Schema] = None
    db_table_service_class = None

    def __init__(self, request: web.Request) -> None:
        super().__init__(request)

        if self.db_table is not None:
            assert self.lookup_field in self.db_table.columns, (
                f"'{self.lookup_field}' is not presented in '{self.db_table.name}' table"
            )

        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_field_value = self.request.match_info.get(lookup_url_kwarg)
        self.kwargs = {
            self.lookup_field: lookup_field_value,
            'partial': self.request.method.lower()
        }
        self.detail = lookup_field_value is not None

        method = self.request.method.lower()
        if method in ['put', 'patch']:
            self.kwargs['partial'] = method == 'patch'

        self.db_service = DatabaseService(engine=self.engine, db_table=self.db_table)

    @property
    def engine(self) -> Engine:
        return self.request.app['db']

    @property
    def user(self) -> typing.Optional[dict]:
        request_property = self.request.app['config'].jwt.request_property
        return self.request[request_property].get('user')

    def get_query(self):
        if self.query is None:
            assert self.db_table is not None, (
                f"'{self.__class__.__name__}' should either include a `query` attribute "
                "or `db_table` attribute or override `get_query()` method"
            )
            self.query = self.db_table.select()
        return self.query

    def get_schema_class(self):
        assert self.schema_class is not None, (
            f"'{self.__class__.__name__}' should either include a `schema_class` "
            "attribute or override `get_schema()` method"
        )
        return self.schema_class

    def get_validation_schema_class(self):
        if self.validation_schema_class is None:
            return self.schema_class
        return self.validation_schema_class

    def get_schema(self, *args, **kwargs) -> Schema:
        schema_class = self.get_schema_class()
        return schema_class(*args, **kwargs)

    def get_validation_schema(self, *args, **kwargs) -> Schema:
        schema_class = self.get_validation_schema_class()
        return schema_class(*args, **kwargs)

    async def get_object(self):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        where_clause = self.db_table.columns[self.lookup_field] == self.kwargs[lookup_url_kwarg]
        query = self.get_query().where(where_clause)
        obj = await self.db_service.execute(query, fetch=FETCH.one)
        if not obj:
            raise web.HTTPNotFound()
        return obj

    async def get_list(self):
        query = self.get_query().limit(self.page_size)
        return await self.db_service.execute(query, fetch=FETCH.all)


class CreateModelMixin:
    async def create(self, *args, **kwargs):
        data = await self.request.text()
        try:
            validated_data = self.get_validation_schema().loads(data)
        except ValidationError as e:
            return web.json_response(e.messages, status=400)

        await self.perform_create(validated_data)
        instance = await self.get_object()
        data = self.get_schema().dump(instance)
        return web.json_response(data)

    async def perform_create(self, validated_data: dict) -> None:
        if self.db_table_service_class:
            await self.db_table_service_class(self.engine).create(validated_data)
        await self.db_service.create(validated_data)


class ListModelMixin:
    async def list(self, *args, **kwargs):
        instances = await self.get_list()
        data = self.get_schema(many=True).dump(instances)
        return web.json_response(data)


class RetrieveModelMixin:
    async def retrieve(self, *args, **kwargs):
        instance = await self.get_object()
        data = self.get_schema().dump(instance)
        return web.json_response(data)


class UpdateModelMixin:
    async def update(self, *args, **kwargs):
        data = await self.request.text()
        schema = self.get_schema()
        try:
            validated_data = schema.loads(data)
        except ValidationError as e:
            return web.json_response(e.messages, status=400)

        instance = await self.get_object()  # may raise 404
        await self.perform_update(instance['id'], validated_data)
        updated_instance = await self.get_object()
        data = schema.dump(updated_instance)

        return web.json_response(data)

    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    async def perform_update(self, id: typing.Any, validated_data: dict):
        if self.db_table_service_class:
            await self.db_table_service_class(self.engine).update(id, validated_data, dump=False)
            return
        await self.db_service.update(validated_data, self.db_table.c.id == id)


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
