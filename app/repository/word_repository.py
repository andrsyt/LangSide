from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.helpers.text_utils import canonical_english_word_key
from app.models.word import DifficultyLevel, StudyStatus, Word
from app.repository.base import BaseRepository
from app.schemas.word import WordCreate, WordUpdate


class WordRepository(BaseRepository[Word, WordCreate, WordUpdate]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Word)

    async def get_by_id_for_user(self, word_id: int, user_id: int) -> Word | None:
        query = select(Word).where(Word.id == word_id, Word.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_text_for_user(self, user_id: int, word_text: str) -> Word | None:
        normalized = canonical_english_word_key(word_text)
        if not normalized:
            return None
        query = select(Word).where(
            Word.user_id == user_id,
            func.lower(Word.word_text) == normalized,
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        user_id: int,
        search: str | None = None,
        difficulty: DifficultyLevel | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        skip: int = 0,
        limit: int | None = None,
    ) -> list[Word]:
        query = select(Word).where(Word.user_id == user_id)
        if search:
            query = query.where(
                or_(
                    Word.word_text.ilike(f"%{search}%"),
                    Word.translation.ilike(f"%{search}%"),
                )
            )
        if difficulty is not None:
            query = query.where(Word.difficulty == difficulty)
        if date_from is not None:
            query = query.where(Word.created_at >= date_from)
        if date_to is not None:
            query = query.where(Word.created_at <= date_to)
        query = query.offset(skip)
        if limit is not None:
            query = query.limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def list_selected_for_test(
        self,
        user_id: int,
        difficulty: DifficultyLevel | None = None,
    ) -> list[Word]:
        query = select(Word).where(
            Word.user_id == user_id,
            Word.is_selected_for_test.is_(True),
        )
        if difficulty is not None:
            query = query.where(Word.difficulty == difficulty)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def list_to_learn(self, user_id: int) -> list[Word]:
        query = select(Word).where(Word.user_id == user_id, Word.study_status == StudyStatus.LEARNING)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def list_by_ids_for_user(self, user_id: int, word_ids: list[int]) -> list[Word]:
        if not word_ids:
            return []
        query = select(Word).where(Word.user_id == user_id, Word.id.in_(word_ids))
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create_for_user(self, user_id: int, word: WordCreate) -> Word:
        db_word = Word(user_id=user_id, **word.model_dump())
        self.db.add(db_word)
        return db_word

    async def list_due_for_user(
        self,
        user_id: int,
        now: datetime,
        limit: int,
        exclude_ids: list[int] | None = None,
        require_translation: bool = False,
        random_order: bool = False,
    ) -> list[Word]:
        query = select(Word).where(
            Word.user_id == user_id,
            Word.next_review_at.isnot(None),
            Word.next_review_at <= now,
        )
        if require_translation:
            query = query.where(Word.translation.isnot(None))
        if exclude_ids:
            query = query.where(Word.id.notin_(exclude_ids))
        if random_order:
            query = query.order_by(func.random())
        else:
            query = query.order_by(Word.next_review_at.asc())
        query = query.limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def list_learning_words(
        self,
        user_id: int,
        limit: int | None = None,
        exclude_ids: list[int] | None = None,
        require_translation: bool = False,
        only_unreviewed: bool = False,
        random_order: bool = False,
        rotate_by_today: bool = False,
    ) -> list[Word]:
        query = select(Word).where(
            Word.user_id == user_id,
            Word.study_status == StudyStatus.LEARNING,
        )
        if require_translation:
            query = query.where(Word.translation.isnot(None))
        if only_unreviewed:
            query = query.where(
                (Word.review_count == 0) | (Word.review_count.is_(None))
            )
        if exclude_ids:
            query = query.where(Word.id.notin_(exclude_ids))
        if rotate_by_today:
            query = query.order_by(
                Word.last_today_session_at.is_(None).desc(),
                Word.last_today_session_at.asc(),
                func.random(),
            )
        elif random_order:
            query = query.order_by(func.random())
        else:
            query = query.order_by(Word.created_at.asc())
        if limit is not None:
            query = query.limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def count_for_user(self, user_id: int) -> int:
        result = await self.db.execute(
            select(func.count(Word.id)).where(Word.user_id == user_id)
        )
        return int(result.scalar() or 0)

    async def count_created_between(
        self,
        user_id: int,
        start: datetime,
        end: datetime,
    ) -> int:
        """Count words created in ``[start, end)``."""
        result = await self.db.execute(
            select(func.count(Word.id)).where(
                Word.user_id == user_id,
                Word.created_at >= start,
                Word.created_at < end,
            )
        )
        return int(result.scalar() or 0)

    async def delete(self, word: Word) -> None:
        await self.db.delete(word)
        await self.db.flush()

    async def count_by_status_for_user(
        self,
        user_id: int,
        study_status: StudyStatus,
    ) -> int:
        result = await self.db.execute(
            select(func.count(Word.id)).where(
                Word.user_id == user_id,
                Word.study_status == study_status,
            )
        )
        return int(result.scalar() or 0)

    async def count_due_for_user_until(
        self,
        user_id: int,
        until: datetime,
    ) -> int:
        result = await self.db.execute(
            select(func.count(Word.id)).where(
                Word.user_id == user_id,
                Word.next_review_at.isnot(None),
                Word.next_review_at <= until,
            )
        )
        return int(result.scalar() or 0)

    async def touch_last_today_session(
        self,
        user_id: int,
        word_ids: list[int],
        when: datetime,
    ) -> None:
        if not word_ids:
            return
        result = await self.db.execute(
            select(Word).where(Word.user_id == user_id, Word.id.in_(word_ids))
        )
        for word in result.scalars().all():
            word.last_today_session_at = when

    async def get_average_knowledge_level_for_user(self, user_id: int) -> float:
        result = await self.db.execute(
            select(func.avg(Word.knowledge_level)).where(Word.user_id == user_id)
        )
        return float(result.scalar() or 0.0)