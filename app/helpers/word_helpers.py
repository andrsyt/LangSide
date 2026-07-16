"""Word access, language preference, and validation."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.http import NotFoundError, UnprocessableEntityError
from app.core.language_codes import default_language_code, resolve_canonical_language_code
from app.helpers.text_utils import (
    canonical_english_word_key,
    normalize_cefr_input,
    parse_explicit_cefr_level,
)
from app.models.word import DifficultyLevel, Word
from app.repository.user_repository import UserRepository
from app.repository.word_repository import WordRepository


class WordAccessService:
    """Provides user-scoped access to word entities."""

    def __init__(self, db: AsyncSession, user_id: int):
        self.user_id = user_id
        self.words = WordRepository(db)

    async def get_word_or_404(self, word_id: int) -> Word:
        word = await self.words.get_by_id_for_user(word_id, self.user_id)
        if word is None:
            raise NotFoundError("Word not found", error_code="WORD_NOT_FOUND")
        return word


class UserLanguageResolver:
    """Resolves the current user's preferred language."""

    def __init__(self, db: AsyncSession, user_id: int):
        self.user_id = user_id
        self.users = UserRepository(db)

    async def get_user_target_language(self) -> str:
        pref = await self.users.get_preferred_language(self.user_id)
        if not pref:
            return default_language_code()
        return resolve_canonical_language_code(pref) or default_language_code()


class WordValidationService:
    """Contains normalization and validation rules for words."""

    @staticmethod
    def normalize_word_text(value: str) -> str:
        return canonical_english_word_key(value)

    @staticmethod
    def parse_difficulty(value: str | None) -> DifficultyLevel | None:
        if value is None:
            return None
        normalized = normalize_cefr_input(str(value))
        if not normalized:
            return None
        level = parse_explicit_cefr_level(normalized)
        if level is not None:
            return level
        raise UnprocessableEntityError(
            "Invalid difficulty. Use one of: A1, A2, B1, B2, C1, C2",
            error_code="INVALID_DIFFICULTY",
        )
