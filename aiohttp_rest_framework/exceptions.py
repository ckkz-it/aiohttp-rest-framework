import json

from aiohttp import hdrs, web

__all__ = [
    "AioRestException",
    "ObjectNotFound",
    "MultipleObjectsReturned",
    "ValidationError",
    "HTTPNotFound",
]


class AioRestException(Exception):
    """Base class for aiohttp-rest-framework errors"""


class DatabaseException(AioRestException):
    """All database related exceptions"""


class ObjectNotFound(DatabaseException):
    """Database service returned 0 object on `get` method call"""


class MultipleObjectsReturned(DatabaseException):
    """Database service returned more than one object on `get` method call"""


class ValidationError(web.HTTPBadRequest):
    """Like ma's ValidationError`, but raises Http 400"""

    def __init__(self, detail=None, **kwargs):
        super().__init__(**kwargs)
        self._headers[hdrs.CONTENT_TYPE] = "application/json"
        self.text = json.dumps(detail)


class HTTPNotFound(web.HTTPNotFound):
    def __init__(self, detail: str = None, **kwargs):
        super().__init__(**kwargs)
        self._headers[hdrs.CONTENT_TYPE] = "application/json"
        self.text = json.dumps({"error": detail or "Not found"})
