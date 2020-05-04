from aiohttp_rest_framework import fields
from aiohttp_rest_framework.serializers import ModelSerializer
from tests import models


class UserSerializer(ModelSerializer):
    password = fields.Str(load_only=True, required=False)
    company_id = fields.Str(required=False)

    class Meta:
        model = models.users
        fields = "__all__"
        dump_only = ("created_at",)
