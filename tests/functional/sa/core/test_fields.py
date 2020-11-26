from aiohttp.test_utils import unittest_run_loop

from aiohttp_rest_framework.fields import sa_ma_pg_field_mapping
from aiohttp_rest_framework.serializers import ModelSerializer
from aiohttp_rest_framework.utils import ClassLookupDict
from tests.functional.sa.core.base import BaseTestCase
from tests.functional.sa.utils import get_fixtures_by_name
from tests.test_app.sa.orm import models


class SASerializer(ModelSerializer):
    class Meta:
        model = models.SAField
        fields = "__all__"


class FieldsTestCase(BaseTestCase):
    @unittest_run_loop
    async def test_pg_sa_inferred_field_serialization(self) -> None:
        reversed_field_mapping = reversed(ClassLookupDict(sa_ma_pg_field_mapping))
        serializer = SASerializer(self.sa_instance)
        self.assertTrue(bool(serializer.data))
        for field in serializer.fields.values():
            self.assertIn(field, reversed_field_mapping)

    @unittest_run_loop
    async def test_pg_sa_inferred_field_deserialization(self) -> None:
        sa_fields_data = get_fixtures_by_name("SAField")[0]
        serializer = SASerializer(data=sa_fields_data)
        serializer.is_valid(raise_exception=True)
        await serializer.save()
