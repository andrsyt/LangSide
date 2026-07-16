"""FastAPI handlers: ``AppBaseException`` and request validation errors."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions.base_exception import AppBaseException

logger = logging.getLogger(__name__)


def _error_body(
    *,
    error_code: str,
    message: str,
    details: dict[str, Any] | list[Any] | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {"error": error_code, "message": message}
    if details is not None:
        body["details"] = details
    return body


async def app_base_exception_handler(
    request: Request,
    exc: AppBaseException,
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body(
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
        ),
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Normalize legacy ``HTTPException`` to the same JSON shape as ``AppBaseException``."""
    detail = exc.detail
    message: str
    details: dict[str, Any] | list[Any] | None = None
    if isinstance(detail, str):
        message = detail
    elif isinstance(detail, dict):
        message = str(detail.get("message") or detail.get("msg") or "Request failed")
        details = detail
    elif isinstance(detail, list):
        message = "Request failed"
        details = detail
    else:
        message = str(detail)

    code = {
        status.HTTP_400_BAD_REQUEST: "BAD_REQUEST",
        status.HTTP_401_UNAUTHORIZED: "UNAUTHORIZED",
        status.HTTP_403_FORBIDDEN: "FORBIDDEN",
        status.HTTP_404_NOT_FOUND: "NOT_FOUND",
        status.HTTP_409_CONFLICT: "CONFLICT",
        status.HTTP_410_GONE: "GONE",
        status.HTTP_422_UNPROCESSABLE_ENTITY: "UNPROCESSABLE_ENTITY",
        status.HTTP_429_TOO_MANY_REQUESTS: "RATE_LIMITED",
        status.HTTP_500_INTERNAL_SERVER_ERROR: "INTERNAL_ERROR",
        status.HTTP_501_NOT_IMPLEMENTED: "NOT_IMPLEMENTED",
        status.HTTP_502_BAD_GATEWAY: "BAD_GATEWAY",
        status.HTTP_503_SERVICE_UNAVAILABLE: "SERVICE_UNAVAILABLE",
    }.get(exc.status_code, "HTTP_ERROR")

    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body(error_code=code, message=message, details=details),
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=_error_body(
            error_code="VALIDATION_ERROR",
            message="Request validation failed",
            details=exc.errors(),
        ),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_error_body(
            error_code="INTERNAL_ERROR",
            message="Internal server error",
            details=None,
        ),
    )


def register_exception_handlers(app) -> None:
    app.add_exception_handler(AppBaseException, app_base_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
