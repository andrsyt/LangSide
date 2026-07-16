"""Opaque refresh tokens: DB stores SHA-256 of the secret; client keeps the raw string."""
from __future__ import annotations


from sqlalchemy.ext.asyncio import AsyncSession

from app.helpers.auth_tokens import RefreshTokenHelper
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repository.refresh_token_repository import RefreshTokenRepository
from app.repository.user_repository import UserRepository
from app.helpers.datetime_utils import utc_naive_now


class RefreshTokenService:
    """Issues, consumes, and revokes opaque refresh tokens."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.refresh_tokens = RefreshTokenRepository(db)
        self.users = UserRepository(db)
        self.token_helper = RefreshTokenHelper()

    async def issue_refresh_token(self, user_id: int) -> str:
        """Create a DB row and return the raw token."""
        raw = self.token_helper.generate_raw_token()
        token_hash = self.token_helper.hash_raw_token(raw)
        expires_at = self.token_helper.build_expires_at()
        await self.refresh_tokens.create(
            RefreshToken(
                user_id=user_id,
                token_hash=token_hash,
                expires_at=expires_at,
            )
        )
        return raw

    async def consume_refresh_token(self, raw: str) -> User | None:
        """
        Validate a raw refresh token, revoke the row, return User for issuing a new token pair.
        """
        if not raw or not raw.strip():
            return None
        token_hash = self.token_helper.hash_raw_token(raw)
        token = await self.refresh_tokens.get_valid_by_hash(token_hash)
        if token is None:
            return None
        user = await self.users.get_active_by_id(token.user_id)
        if user is None:
            return None
        token.revoked_at = utc_naive_now()
        await self.db.flush()
        return user

    async def revoke_refresh_token(self, raw: str) -> bool:
        if not raw or not raw.strip():
            return False
        token_hash = self.token_helper.hash_raw_token(raw)
        token = await self.refresh_tokens.get_active_by_hash(token_hash)
        if token is None:
            return False
        token.revoked_at = utc_naive_now()
        await self.db.flush()
        return True
