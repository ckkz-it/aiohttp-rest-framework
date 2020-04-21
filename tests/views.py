from aiohttp_rest_framework import views
from tests.serializers import UserSerializer


class UserView(views.ListAPIView):
    serializer_class = UserSerializer
