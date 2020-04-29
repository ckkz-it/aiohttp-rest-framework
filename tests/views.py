from aiohttp_rest_framework import views
from tests.serializers import UserSerializer


class UsersListView(views.ListCreateAPIView):
    serializer_class = UserSerializer


class UsersRetrieveUpdateDestroyView(views.RetrieveUpdateDestroyAPIView):
    serializer_class = UserSerializer
