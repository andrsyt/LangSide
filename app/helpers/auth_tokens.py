"""Opaque refresh-token hashing and expiry helpers."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta

from app.core.config import settings
from app.helpers.datetime_utils import utc_naive_now


class RefreshTokenHelper:
    """Builds and hashes opaque refresh token values."""

    @staticmethod
    def hash_raw_token(raw: str) -> str:
        return hashlib.sha256(raw.strip().encode("utf-8")).hexdigest()

    @staticmethod
    def generate_raw_token() -> str:
        return secrets.token_urlsafe(48)

    @staticmethod
    def build_expires_at() -> datetime:
        return utc_naive_now() + timedelta(
            minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
        )
