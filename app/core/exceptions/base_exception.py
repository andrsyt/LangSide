"""Base type for application errors (HTTP-mapped via exception handlers)."""

from __future__ import annotations

from typing import Any


class AppBaseException(Exception):
    """Base exception: ``status_code`` and ``error_code`` are used by API handlers."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: dict[str, Any] | list[Any] | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details
        super().__init__(message)

    def __str__(self) -> str:
        return self.message
