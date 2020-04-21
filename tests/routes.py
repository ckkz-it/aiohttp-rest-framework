from aiohttp import web

from tests.aiopg import views


def setup_routes(app: web.Application):
    app.router.add_view('/user', views.UserView)
