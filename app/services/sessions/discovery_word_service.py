"""Ensure catalog words exist in the user's dictionary for today sessions."""

from __future__ import annotations

import logging

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.today_session_config import TODAY_DISCOVERY_DAILY_MAX
from app.helpers.english_level import levels_for_user
from app.helpers.translation_helper import translate_and_normalize
from app.helpers.word_helpers import UserLanguageResolver, WordValidationService
from app.models.word import DifficultyLevel, StudyStatus, Word
from app.repository.common_word_repository import CommonWordRepository
from app.repository.session_item_repository import SessionItemRepository
from app.repository.word_repository import WordRepository
from app.services.sessions.user_stats_service import UserStatsService
from app.tasks.word_tasks import analyze_user_word_task

logger = logging.getLogger(__name__)

class DiscoveryWordService:
    """Maps common_words catalog entries to user-owned Word rows."""

    def __init__(self, db: AsyncSession, user_id: int):
        self.db = db
        self.user_id = user_id
        self.words = WordRepository(db)
        self.common_words = CommonWordRepository(db)
        self.session_items = SessionItemRepository(db)
        self.language_resolver = UserLanguageResolver(db, user_id)
        self.stats = UserStatsService(db, user_id)

    async def discovery_slots_remaining(self, session_date: date) -> int:
        used = await self.session_items.count_discovery_for_user_on_date(
            self.user_id,
            session_date,
        )
        return max(0, TODAY_DISCOVERY_DAILY_MAX - used)

    async def ensure_word_for_user(
        self,
        word_text: str,
        level: DifficultyLevel,
        *,
        require_translation: bool = True,
    ) -> Word | None:
        normalized = WordValidationService.normalize_word_text(word_text)
        if not normalized:
            return None

        existing = await self.words.get_by_text_for_user(self.user_id, normalized)
        if existing is not None:
            status = getattr(existing.study_status, "value", existing.study_status)
            if status == StudyStatus.MASTERED.value:
                return None
            if require_translation and not existing.translation:
                await self._fill_translation(existing)
                await self.db.flush()
            if require_translation and not existing.translation:
                return None
            if existing.difficulty is None:
                existing.difficulty = level
            if not self._has_intro_content(existing):
                await self._schedule_analysis(existing.id)
            return existing

        translation: str | None = None
        if require_translation:
            translation = await self._translate(normalized)

        if require_translation and not translation:
            return None

        word = Word(
            user_id=self.user_id,
            word_text=normalized,
            translation=translation,
            difficulty=level,
            study_status=StudyStatus.LEARNING.value,
        )
        self.db.add(word)
        await self.db.flush()
        await self.stats.record_word_added()
        await self._schedule_analysis(word.id)
        return word

    async def pick_discovery_words(
        self,
        user_level: DifficultyLevel,
        count: int,
        session_date: date,
        exclude_word_ids: list[int] | None = None,
        exclude_texts: set[str] | None = None,
    ) -> list[Word]:
        if count <= 0:
            return []

        remaining_slots = await self.discovery_slots_remaining(session_date)
        if remaining_slots <= 0:
            return []
        count = min(count, remaining_slots)

        exclude_word_ids = set(exclude_word_ids or [])
        exclude_normalized = {text.strip().lower() for text in (exclude_texts or set()) if text}

        levels = levels_for_user(user_level)
        candidates = await self.common_words.fetch_random_by_levels(
            levels,
            limit=max(count * 5, 15),
            exclude_normalized=exclude_normalized,
        )

        result: list[Word] = []
        for text, level in candidates:
            word = await self.ensure_word_for_user(
                text,
                level,
                require_translation=True,
            )
            if word is None or word.id in exclude_word_ids:
                continue
            if not self._has_intro_content(word):
                continue
            exclude_word_ids.add(word.id)
            exclude_normalized.add(word.word_text.strip().lower())
            result.append(word)
            if len(result) >= count:
                break
        return result

    async def _translate(self, word_text: str) -> str | None:
        lang = await self.language_resolver.get_user_target_language()
        return await translate_and_normalize(word_text, lang)
        
    async def _fill_translation(self, word: Word) -> None:
        translated = await self._translate(word.word_text)
        if translated:
            word.translation = translated

    async def _schedule_analysis(self, word_id: int) -> None:
        try:
            analyze_user_word_task.delay(self.user_id, word_id)
        except Exception as exc:
            logger.warning("Failed to schedule analysis for word %d: %s", word_id, exc)

    @staticmethod
    def _has_intro_content(word: Word) -> bool:
        return bool(word.explanation and word.explanation.strip())
