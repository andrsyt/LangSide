from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.helpers.ai_analysis_helper import VocabularyLookupHelper
from app.models.word import DifficultyLevel


class VocabularyService:
    """
    Service for the CommonWord table: word level and frequency lists.
    """

    def __init__(self, db: AsyncSession):
        self.lookup_helper = VocabularyLookupHelper(db)

    async def get_word_level(self, word: str) -> Optional[DifficultyLevel]:
        """Return the CEFR level of a word from the database."""
        return await self.lookup_helper.get_word_level(word)

    async def get_common_words_by_level(
        self,
        level: DifficultyLevel,
        limit: int = 20,
        exclude_words: Optional[List[str]] = None,
    ) -> List[str]:
        """Return common words for the given CEFR level."""
        return await self.lookup_helper.get_common_words_by_level(
            level,
            limit=limit,
            exclude_words=exclude_words,
        )

    async def is_word_common(self, word: str) -> bool:
        """Return whether the word is marked as everyday/common."""
        return await self.lookup_helper.is_word_common(word)


async def get_word_level(db: AsyncSession, word: str) -> Optional[DifficultyLevel]:
    """
    Wrapper around VocabularyService.get_word_level for legacy API compatibility.
    """
    service = VocabularyService(db)
    return await service.get_word_level(word)


async def get_common_words_by_level(
    db: AsyncSession,
    level: DifficultyLevel,
    limit: int = 20,
    exclude_words: Optional[List[str]] = None,
) -> List[str]:
    """
    Wrapper around VocabularyService.get_common_words_by_level for legacy API compatibility.
    """
    service = VocabularyService(db)
    return await service.get_common_words_by_level(level, limit=limit, exclude_words=exclude_words)
