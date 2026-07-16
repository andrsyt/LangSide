from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import HTTPException, status

from app.services.billing.rules import BillingRulesService
from app.helpers.text_utils import normalize_sentence
from app.helpers.translation_helper import translate_and_normalize
from app.helpers.word_helpers import (
    UserLanguageResolver,
    WordAccessService,
    WordValidationService,
)
from app.models.word import DifficultyLevel, Word
from app.repository.word_repository import WordRepository
from app.schemas.ai import WordAnalysisResponse
from app.schemas.word import WordCreate, WordUpdate
from app.services.users.user_service import UserQueryService
from app.services.sessions.user_stats_service import UserStatsService


class WordQueryService:
    """Read-only use cases for the user's words."""

    def __init__(self, db: AsyncSession, user_id: int):
        self.user_id = user_id
        self.words = WordRepository(db)
        self.word_access = WordAccessService(db, user_id)

    async def get_user_words(
        self,
        search: str | None = None,
        difficulty: DifficultyLevel | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[Word]:
        return await self.words.list_for_user(
            user_id=self.user_id,
            search=search,
            difficulty=difficulty,
            date_from=date_from,
            date_to=date_to,
        )

    async def get_word_by_id(self, word_id: int) -> Word:
        return await self.word_access.get_word_or_404(word_id)

    async def get_words_to_learn(self) -> list[Word]:
        return await self.words.list_to_learn(self.user_id)


class WordCommandService:
    """Write use cases for the user's words."""

    def __init__(self, db: AsyncSession, user_id: int):
        self.db = db
        self.user_id = user_id
        self.words = WordRepository(db)
        self.word_access = WordAccessService(db, user_id)
        self.word_rules = WordValidationService()
        self.billing_rules = BillingRulesService()
        self.user_query = UserQueryService(db)
        self.stats = UserStatsService(db, user_id)

    async def create_word(self, word: WordCreate) -> Word:
        user = await self.user_query.get_user_by_id(self.user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        count = await self.words.count_for_user(self.user_id)
        self.billing_rules.ensure_can_add_word(user=user, word_count=count)

        db_word = await self.words.create(
            {
                "user_id": self.user_id,
                "word_text": self.word_rules.normalize_word_text(word.word_text),
                "translation": None,
                "explanation": None,
                "examples": None,
                "difficulty": None,
            }
        )
        await self.stats.record_word_added()
        await self.db.commit()
        await self.db.refresh(db_word)
        return db_word

    async def update_word(self, word_id: int, word_data: WordUpdate) -> Word:
        word = await self.word_access.get_word_or_404(word_id)
        if word_data.word_text is not None:
            word.word_text = self.word_rules.normalize_word_text(word_data.word_text)
        if word_data.translation is not None:
            word.translation = word_data.translation
        if word_data.explanation is not None:
            word.explanation = word_data.explanation
        if word_data.examples is not None:
            word.examples = word_data.examples
        if word_data.difficulty is not None:
            word.difficulty = self.word_rules.parse_difficulty(word_data.difficulty)
        await self.db.commit()
        await self.db.refresh(word)
        return word

    async def delete_word(self, word_id: int) -> None:
        word = await self.word_access.get_word_or_404(word_id)
        await self.words.delete(word)
        await self.db.commit()


class WordAIAnalysisService:
    """Applies AI analysis results to a word."""

    def __init__(self, db: AsyncSession, user_id: int):
        self.db = db
        self.user_id = user_id
        self.word_access = WordAccessService(db, user_id)
        self.language_resolver = UserLanguageResolver(db, user_id)

    async def update_word_with_ai_analysis(
        self,
        word_id: int,
        ai_analysis: WordAnalysisResponse,
    ) -> Word:
        word = await self.word_access.get_word_or_404(word_id)
        lang = await self.language_resolver.get_user_target_language()
        translate = await translate_and_normalize(word.word_text, lang)

        if translate:
            word.translation = translate

        word.explanation = normalize_sentence(ai_analysis.explanation) or None
        word.examples = (
            "\n".join(
                normalize_sentence(example, max_words=15)
                for example in ai_analysis.examples
                if example
            )
            or None
        )
        if ai_analysis.difficulty:
            try:
                word.difficulty = DifficultyLevel(ai_analysis.difficulty)
            except ValueError:
                word.difficulty = None

        await self.db.commit()
        await self.db.refresh(word)
        return word
