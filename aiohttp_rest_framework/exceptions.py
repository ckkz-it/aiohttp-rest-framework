import json

from aiohttp import web, hdrs


class AioRestException(Exception):
    pass


class ValidationError(web.HTTPBadRequest):
    def __init__(self, detail=None, **kwargs):
        super().__init__(**kwargs)
        self._headers[hdrs.CONTENT_TYPE] = 'application/json'
        self.text = json.dumps(detail)
