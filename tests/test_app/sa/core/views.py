from aiohttp_rest_framework import views
from tests.test_app.sa.orm.serializers import UserSerializer


class UsersListCreateView(views.ListCreateAPIView):
    serializer_class = UserSerializer


class UsersRetrieveUpdateDestroyView(views.RetrieveUpdateDestroyAPIView):
    serializer_class = UserSerializer
