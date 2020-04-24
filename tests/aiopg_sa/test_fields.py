import asyncio

from aiopg.sa.result import RowProxy

from aiohttp_rest_framework.fields import sa_ma_pg_field_mapping
from aiohttp_rest_framework.serializers import ModelSerializer
from aiohttp_rest_framework.utils import ClassLookupDict
from tests import models
from tests.aiopg_sa.utils import (
    create_data_fixtures,
    create_pg_db,
    create_tables,
    drop_pg_db,
    drop_tables,
)
from tests.config import db


def setup_module():
    create_pg_db(db_name=db["database"])


def teardown_module():
    drop_pg_db(db_name=db["database"])


def setup_function():
    create_tables()
    loop = asyncio.new_event_loop()
    loop.run_until_complete(create_data_fixtures())
    loop.close()


def teardown_function():
    drop_tables()


class AioPGSASerializer(ModelSerializer):
    class Meta:
        model = models.aiopg_sa_fields
        fields = "__all__"


async def test_aiopg_sa_inferred_field_serialization(aiopg_sa_instance: RowProxy):
    reversed_class_lookup_dict = reversed(ClassLookupDict(sa_ma_pg_field_mapping))
    serializer = AioPGSASerializer(aiopg_sa_instance)
    assert serializer.data
    for _, field in serializer.fields.items():
        actual_field = field._field
        assert actual_field in reversed_class_lookup_dict
