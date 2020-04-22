from marshmallow import fields

from aiohttp_rest_framework.serializers import ModelSerializer
from tests import models


class UserCreateSerializer(ModelSerializer):
    id = fields.UUID(dump_only=True)
    name = fields.Str(required=True)
    email = fields.Str(required=True)
    phone = fields.Str(required=True)
    password = fields.Str(required=True)

    class Meta:
        model = models.users


class UserSerializer(ModelSerializer):
    id = fields.UUID(dump_only=True)
    name = fields.Str()
    email = fields.Str()
    phone = fields.Str()
    created_at = fields.DateTime(dump_only=True)

    class Meta:
        model = models.users
