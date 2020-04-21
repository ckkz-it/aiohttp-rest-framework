from aiohttp import web

from tests import views


def setup_routes(app: web.Application):
    app.router.add_view("/users", views.UserView)
