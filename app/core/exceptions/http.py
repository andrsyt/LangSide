"""HTTP-oriented exceptions used across API, services, and helpers."""

from __future__ import annotations

from typing import Any

from app.core.exceptions.base_exception import AppBaseException


class BadRequestError(AppBaseException):
    """400 — invalid input or business rule (e.g. session already finished)."""

    def __init__(
        self,
        message: str,
        *,
        error_code: str = "BAD_REQUEST",
        details: dict[str, Any] | list[Any] | None = None,
    ) -> None:
        super().__init__(
            message,
            status_code=400,
            error_code=error_code,
            details=details,
        )


class UnauthorizedError(AppBaseException):
    """401 — missing or invalid credentials / token."""

    def __init__(
        self,
        message: str = "Unauthorized",
        *,
        error_code: str = "UNAUTHORIZED",
        details: dict[str, Any] | list[Any] | None = None,
    ) -> None:
        super().__init__(
            message,
            status_code=401,
            error_code=error_code,
            details=details,
        )


class ForbiddenError(AppBaseException):
    """403 — authenticated but not allowed."""

    def __init__(
        self,
        message: str = "Forbidden",
        *,
        error_code: str = "FORBIDDEN",
        details: dict[str, Any] | list[Any] | None = None,
    ) -> None:
        super().__init__(
            message,
            status_code=403,
            error_code=error_code,
            details=details,
        )


class NotFoundError(AppBaseException):
    """404 — word, user, session, exercise, card, etc."""

    def __init__(
        self,
        message: str = "Not found",
        *,
        error_code: str = "NOT_FOUND",
        details: dict[str, Any] | list[Any] | None = None,
    ) -> None:
        super().__init__(
            message,
            status_code=404,
            error_code=error_code,
            details=details,
        )


class ConflictError(AppBaseException):
    """409 — duplicate email/username, conflicting state."""

    def __init__(
        self,
        message: str,
        *,
        error_code: str = "CONFLICT",
        details: dict[str, Any] | list[Any] | None = None,
    ) -> None:
        super().__init__(
            message,
            status_code=409,
            error_code=error_code,
            details=details,
        )


class GoneError(AppBaseException):
    """410 — exercise already consumed / no longer valid for retry."""

    def __init__(
        self,
        message: str = "Resource is no longer available",
        *,
        error_code: str = "GONE",
        details: dict[str, Any] | list[Any] | None = None,
    ) -> None:
        super().__init__(
            message,
            status_code=410,
            error_code=error_code,
            details=details,
        )


class UnprocessableEntityError(AppBaseException):
    """422 — semantic validation (e.g. invalid difficulty enum string)."""

    def __init__(
        self,
        message: str,
        *,
        error_code: str = "UNPROCESSABLE_ENTITY",
        details: dict[str, Any] | list[Any] | None = None,
    ) -> None:
        super().__init__(
            message,
            status_code=422,
            error_code=error_code,
            details=details,
        )


class TooManyRequestsError(AppBaseException):
    """429 — billing / usage rate limit."""

    def __init__(
        self,
        message: str = "Too many requests",
        *,
        error_code: str = "RATE_LIMITED",
        details: dict[str, Any] | list[Any] | None = None,
    ) -> None:
        super().__init__(
            message,
            status_code=429,
            error_code=error_code,
            details=details,
        )


class InternalServerError(AppBaseException):
    """500 — unexpected failure or misconfiguration (e.g. missing API key)."""

    def __init__(
        self,
        message: str = "Internal server error",
        *,
        error_code: str = "INTERNAL_ERROR",
        details: dict[str, Any] | list[Any] | None = None,
    ) -> None:
        super().__init__(
            message,
            status_code=500,
            error_code=error_code,
            details=details,
        )


class BadGatewayError(AppBaseException):
    """502 — upstream provider failure (Groq, translation API, etc.)."""

    def __init__(
        self,
        message: str = "Bad gateway",
        *,
        error_code: str = "BAD_GATEWAY",
        details: dict[str, Any] | list[Any] | None = None,
    ) -> None:
        super().__init__(
            message,
            status_code=502,
            error_code=error_code,
            details=details,
        )


class ServiceUnavailableError(AppBaseException):
    """503 — dependency temporarily unavailable."""

    def __init__(
        self,
        message: str = "Service unavailable",
        *,
        error_code: str = "SERVICE_UNAVAILABLE",
        details: dict[str, Any] | list[Any] | None = None,
    ) -> None:
        super().__init__(
            message,
            status_code=503,
            error_code=error_code,
            details=details,
        )


class NotImplementedAPIError(AppBaseException):
    """501 — feature stub (e.g. App Store verification not implemented yet)."""

    def __init__(
        self,
        message: str = "Not implemented",
        *,
        error_code: str = "NOT_IMPLEMENTED",
        details: dict[str, Any] | list[Any] | None = None,
    ) -> None:
        super().__init__(
            message,
            status_code=501,
            error_code=error_code,
            details=details,
        )
