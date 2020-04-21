from marshmallow import fields

from aiohttp_rest_framework.serializers import ModelSerializer
from tests import models


class UserSerializer(ModelSerializer):
    id = fields.UUID(dump_only=True)
    name = fields.Str()
    email = fields.Str()
    phone = fields.Str()
    password = fields.Str(load_only=True)
    created_at = fields.DateTime(dump_only=True)

    class Meta:
        model = models.user
