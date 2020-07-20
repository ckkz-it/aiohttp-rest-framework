import json

from aiohttp import hdrs, web

__all__ = [
    "AioRestException",
    "DatabaseException",
    "ObjectNotFound",
    "MultipleObjectsReturned",
    "FieldValidationError",
    "UniqueViolationError",
    "ValidationError",
    "HTTPNotFound",
]


class AioRestException(Exception):
    """Base class for aiohttp-rest-framework errors"""

    def __init__(self, message: str = "Unhandled rest-framework exception"):
        self.message = message


class DatabaseException(AioRestException):
    """All database related exceptions"""

    def __init__(self, message: str = "Database exception"):
        super().__init__(message)


class ObjectNotFound(DatabaseException):
    """Database service returned 0 object on `get` method call"""

    def __init__(self, message: str = "Object not found"):
        super().__init__(message)


class MultipleObjectsReturned(DatabaseException):
    """Database service returned more than one object on `get` method call"""

    def __init__(self, message: str = "Multiple objects returned"):
        super().__init__(message)


class FieldValidationError(DatabaseException):
    """Invalid field value provided to the model's field"""

    def __init__(self, message: str = "Invalid field value"):
        super().__init__(message)


class UniqueViolationError(DatabaseException):
    """Unique constraint violation"""

    def __init__(self, message: str = "Unique violation error"):
        super().__init__(message)


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
