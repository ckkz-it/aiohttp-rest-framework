import asyncio

from aiohttp_rest_framework.fields import sa_ma_pg_field_mapping
from aiohttp_rest_framework.serializers import ModelSerializer
from aiohttp_rest_framework.utils import ClassLookupDict
from tests import models
from tests.config import db
from tests.pg_sa.utils import create_data_fixtures, create_db, create_tables, drop_db, drop_tables


def setup_module():
    loop = asyncio.new_event_loop()
    loop.run_until_complete(create_db(db_name=db["database"]))
    loop.close()


def teardown_module():
    loop = asyncio.new_event_loop()
    loop.run_until_complete(drop_db(db_name=db["database"]))
    loop.close()


def setup_function():
    create_tables()
    loop = asyncio.new_event_loop()
    loop.run_until_complete(create_data_fixtures())
    loop.close()


def teardown_function():
    drop_tables()


class PGSASerializer(ModelSerializer):
    class Meta:
        model = models.pg_sa_fields
        fields = "__all__"


async def test_pg_sa_inferred_field_serialization(pg_sa_instance):
    reversed_field_mapping = reversed(ClassLookupDict(sa_ma_pg_field_mapping))
    serializer = PGSASerializer(pg_sa_instance)
    assert serializer.data
    for field in serializer.fields.values():
        assert field in reversed_field_mapping


async def test_pg_sa_inferred_field_deserialization(get_fixtures_by_name, client):
    sa_fields_data = get_fixtures_by_name("pg_sa_fields")[0]
    serializer = PGSASerializer(data=sa_fields_data)
    serializer.is_valid(raise_exception=True)
    await serializer.save()
