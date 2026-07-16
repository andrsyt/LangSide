"""404-safe word access and repeat-specific validation."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.http import BadRequestError
from app.helpers.word_helpers import WordAccessService
from app.models.word import Word


class RepeatAccessService:
    """Provides 404-safe word access and repeat-specific validation."""

    def __init__(self, db: AsyncSession, user_id: int):
        self._word_access = WordAccessService(db, user_id)

    async def get_word_or_404(self, word_id: int) -> Word:
        return await self._word_access.get_word_or_404(word_id)

    @staticmethod
    def ensure_word_has_translation(word: Word) -> None:
        if not word.translation:
            raise BadRequestError(
                "Word has no translation. Run AI analysis first via "
                "POST /words/{word_id}/analyze",
                error_code="WORD_TRANSLATION_REQUIRED",
            )
