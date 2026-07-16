from __future__ import annotations

from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.helpers.repeat import RepeatAccessService
from app.models.word import StudyStatus, Word
from app.repository.word_repository import WordRepository
from app.helpers.datetime_utils import utc_naive_now


class RepeatQueryService:
    """Read-only use cases for word repetition."""

    def __init__(self, db: AsyncSession, user_id: int):
        self.user_id = user_id
        self.words = WordRepository(db)

    async def get_words_to_repeat(self, limit: int = 20) -> list[Word]:
        return await self.words.list_due_for_user(
            user_id=self.user_id,
            now=utc_naive_now(),
            limit=limit,
        )


class RepeatCommandService:
    """Write use cases for word repetition."""

    def __init__(self, db: AsyncSession, user_id: int):
        self.db = db
        self.user_id = user_id
        self.access = RepeatAccessService(db, user_id)

    async def reset_word_progress(self, word_id: int) -> Word:
        word = await self.access.get_word_or_404(word_id)
        word.study_status = StudyStatus.LEARNING
        word.knowledge_level = 0
        word.review_count = 0
        word.correct_count = 0
        word.incorrect_count = 0
        word.ease_factor = 2.5
        word.last_reviewed_at = None
        word.next_review_at = None
        await self.db.commit()
        await self.db.refresh(word)
        return word

    async def mark_word_mastered(self, word_id: int) -> Word:
        word = await self.access.get_word_or_404(word_id)
        word.study_status = StudyStatus.MASTERED
        if word.knowledge_level is None or word.knowledge_level < 5:
            word.knowledge_level = 5
        word.last_reviewed_at = utc_naive_now()
        word.next_review_at = utc_naive_now() + timedelta(days=30)
        await self.db.commit()
        await self.db.refresh(word)
        return word


class RepeatService:
    """Object wrapper over repeat query and command use cases."""

    def __init__(self, db: AsyncSession, user_id: int):
        self.queries = RepeatQueryService(db, user_id)
        self.commands = RepeatCommandService(db, user_id)

    async def get_words_to_repeat(self, limit: int = 20) -> list[Word]:
        return await self.queries.get_words_to_repeat(limit)

    async def reset_word_progress(self, word_id: int) -> Word:
        return await self.commands.reset_word_progress(word_id)

    async def mark_word_mastered(self, word_id: int) -> Word:
        return await self.commands.mark_word_mastered(word_id)
