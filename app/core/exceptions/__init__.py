"""Application exceptions and FastAPI handler registration."""

from app.core.exceptions.base_exception import AppBaseException
from app.core.exceptions.handlers import register_exception_handlers
from app.core.exceptions.http import (
    BadGatewayError,
    BadRequestError,
    ConflictError,
    ForbiddenError,
    GoneError,
    InternalServerError,
    NotFoundError,
    NotImplementedAPIError,
    ServiceUnavailableError,
    TooManyRequestsError,
    UnauthorizedError,
    UnprocessableEntityError,
)

__all__ = [
    "AppBaseException",
    "BadGatewayError",
    "BadRequestError",
    "ConflictError",
    "ForbiddenError",
    "GoneError",
    "InternalServerError",
    "NotFoundError",
    "NotImplementedAPIError",
    "ServiceUnavailableError",
    "TooManyRequestsError",
    "UnauthorizedError",
    "UnprocessableEntityError",
    "register_exception_handlers",
]
