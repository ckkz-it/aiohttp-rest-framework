import json

from aiohttp import hdrs, web


class AioRestException(Exception):
    """ Base class for aiohttp-rest-framework errors """


class ValidationError(web.HTTPBadRequest):
    """ Like ma's ValidationError`, but raises Http 400 """

    def __init__(self, detail=None, **kwargs):
        super().__init__(**kwargs)
        self._headers[hdrs.CONTENT_TYPE] = "application/json"
        self.text = json.dumps(detail)


class ObjectNotFound(web.HTTPNotFound):
    def __init__(self, detail: str = None, **kwargs):
        super().__init__(**kwargs)
        self._headers[hdrs.CONTENT_TYPE] = "application/json"
        self.text = json.dumps({"error": detail or "Not found"})
