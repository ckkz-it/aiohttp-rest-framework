import asyncio

import pytest
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
    reversed_field_mapping = reversed(ClassLookupDict(sa_ma_pg_field_mapping))
    serializer = AioPGSASerializer(aiopg_sa_instance)
    assert serializer.data
    for field in serializer.fields.values():
        assert field in reversed_field_mapping


# pass here client to initialize app's db property (will be needed to create instance)
# @pytest.mark.parametrize("interval", [
#     "3 hours 2 minutes 3 seconds", "3 hours 3 seconds", 86400
# ])
async def test_aiopg_sa_inferred_field_deserialization(get_fixtures_by_name, client):
    sa_fields_data = get_fixtures_by_name("aiopg_sa_fields")[0]
    # sa_fields_data["Interval"] = interval
    serializer = AioPGSASerializer(data=sa_fields_data)
    serializer.is_valid(raise_exception=True)
    await serializer.save()
