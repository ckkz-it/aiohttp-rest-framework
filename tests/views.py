from aiohttp import hdrs

from aiohttp_rest_framework import views
from tests.serializers import UserCreateSerializer, UserSerializer


class UsersListView(views.ListCreateAPIView):
    def get_serializer_class(self):
        if self.request.method == hdrs.METH_GET:
            return UserSerializer
        return UserCreateSerializer


class UsersRetrieveUpdateDestroyView(views.RetrieveUpdateDestroyAPIView):
    serializer_class = UserSerializer
