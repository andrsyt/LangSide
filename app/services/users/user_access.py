"""User lookup, validation, and language-sync for the users domain."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.http import BadRequestError, NotFoundError
from app.core.language_codes import resolve_canonical_language_code
from app.helpers.translation_helper import translate_and_normalize
from app.models.user import User
from app.repository.user_repository import UserRepository
from app.repository.word_repository import WordRepository


class UserAccessService:
    """Provides user lookup helpers with 404 handling."""

    def __init__(self, db: AsyncSession):
        self.users = UserRepository(db)

    async def get_user_or_404(self, user_id: int) -> User:
        user = await self.users.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found", error_code="USER_NOT_FOUND")
        return user


class UserLanguageSyncService:
    """Synchronizes dependent word translations after language changes."""

    def __init__(self, db: AsyncSession):
        self.words = WordRepository(db)

    async def sync_word_translations_for_user(
        self,
        user_id: int,
        target_language: str,
    ) -> int:
        """Re-translate all user words to the canonical target language."""
        words = await self.words.list_for_user(user_id)
        canonical = resolve_canonical_language_code(target_language)
        if canonical is None:
            return 0

        updated = 0
        for word in words:
            translated = await translate_and_normalize(word.word_text, canonical)
            if translated:
                word.translation = translated
                updated += 1
        return updated


class UserValidationService:
    """Contains validation rules for user mutations."""

    def __init__(self, db: AsyncSession):
        self.users = UserRepository(db)

    async def ensure_email_is_unique(
        self,
        email: str,
        exclude_user_id: int | None = None,
    ) -> None:
        existing_user = await self.users.get_by_email(email)
        if existing_user and existing_user.id != exclude_user_id:
            raise BadRequestError(
                "Email already registered",
                error_code="EMAIL_ALREADY_REGISTERED",
            )

    async def ensure_username_is_unique(
        self,
        username: str,
        exclude_user_id: int | None = None,
    ) -> None:
        existing_user = await self.users.get_by_username(username)
        if existing_user and existing_user.id != exclude_user_id:
            raise BadRequestError(
                "Username already registered",
                error_code="USERNAME_ALREADY_REGISTERED",
            )
