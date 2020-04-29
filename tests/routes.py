import aiohttp_cors
from aiohttp import web

from tests import views


def setup_routes(app: web.Application):
    app.router.add_view("/users", views.UsersListCreateView)
    app.router.add_view("/users/{id}", views.UsersRetrieveUpdateDestroyView)

    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
        )
    })

    for route in app.router.routes():
        cors.add(route)
