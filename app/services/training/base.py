from __future__ import annotations

import asyncio

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from localization.get_synonyms import get_synonyms_with_auto_fill

from app.core.exceptions.http import UnprocessableEntityError
from app.core.language_codes import default_language_code, resolve_canonical_language_code
from app.helpers.training_helpers import TrainingAccessService, TrainingContentHelper
from app.helpers.translation_helper import translate_and_normalize
from app.helpers.text_utils import normalize_sentence
from app.models.word import Word
from app.schemas.training import WordIntroInfo
from app.services.words.ai_service import AIAnalysisService
from app.services.users.user_service import UserQueryService
from app.services.words.word_service import WordAIAnalysisService, WordQueryService
from app.tasks.word_tasks import analyze_user_word_task

logger = logging.getLogger(__name__)


class TrainingBaseService:
    """Common dependencies and orchestration helpers for training flows."""

    def __init__(self, db: AsyncSession, user_id: int):
        self.db = db
        self.user_id = user_id
        self.access = TrainingAccessService(db, user_id)
        self.ai_analysis = AIAnalysisService(db)
        self.user_queries = UserQueryService(db)
        self.word_queries = WordQueryService(db, user_id)
        self.word_ai = WordAIAnalysisService(db, user_id)

    async def get_word(self, word_id: int) -> Word:
        return await self.word_queries.get_word_by_id(word_id)

    async def get_user_language(self) -> str:
        user = await self.user_queries.get_user_by_id(self.user_id)
        if user is None or not user.preferred_language:
            return default_language_code()
        return resolve_canonical_language_code(user.preferred_language) or default_language_code()

    async def get_learning_words_except(self, word_id: int) -> list[Word]:
        return [
            word
            for word in await self.word_queries.get_words_to_learn()
            if word.id != word_id
        ]

    async def ensure_word_analyzed(self, word_id: int) -> None:
        word = await self.get_word(word_id)
        examples = TrainingContentHelper.parse_examples(word.examples)
        if examples and word.explanation:
            return

        self._schedule_analysis(word_id)
        
    async def build_word_intro_info(self, word_id: int) -> WordIntroInfo:
        await self.ensure_word_analyzed(word_id)
        word = await self.get_word(word_id)
        explanation = normalize_sentence(word.explanation) or None
        if explanation is None:
            raise UnprocessableEntityError(
                "Word is still being prepared",
                error_code="WORD_NOT_READY",
            )

        lang = await self.get_user_language()
        translation = await translate_and_normalize(word.word_text, lang)
        examples = [
            normalized
            for example in TrainingContentHelper.parse_examples(word.examples)
            if (normalized := normalize_sentence(example, max_words=15))
        ]
        synonyms = await asyncio.to_thread(get_synonyms_with_auto_fill, word.word_text)
        return WordIntroInfo(
            translation=translation or "",
            examples=examples,
            synonyms=synonyms,
            explanation=explanation,
        )

    def _schedule_analysis(self, word_id: int) -> None:
        try:
            analyze_user_word_task.delay(self.user_id, word_id)
        except Exception as exc:
            logger.warning("Failed to schedule analysis for word %d: %s", word_id, exc)
