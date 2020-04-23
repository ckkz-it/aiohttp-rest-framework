from aiohttp_rest_framework.serializers import ModelSerializer
from tests import models


class UserCreateSerializer(ModelSerializer):
    class Meta:
        model = models.users
        fields = ("id", "name", "email", "phone", "password")


class UserSerializer(ModelSerializer):
    class Meta:
        model = models.users
        fields = ("id", "name", "email", "phone", "created_at")
