from datetime import date, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.learning_session import LearningSession, LearningSessionItem
from app.models.word import Word


class LearningSessionItemRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_many(self, items: list[LearningSessionItem]) -> list[LearningSessionItem]:
        self.db.add_all(items)
        return items

    async def get_by_id_in_session(
        self,
        session_id: int,
        item_id: int,
    ) -> LearningSessionItem | None:
        result = await self.db.execute(
            select(LearningSessionItem).where(
                LearningSessionItem.learning_session_id == session_id,
                LearningSessionItem.id == item_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_with_word_text(
        self,
        learning_session_id: int,
    ) -> list[tuple[LearningSessionItem, str]]:
        result = await self.db.execute(
            select(LearningSessionItem, Word.word_text)
            .join(Word, Word.id == LearningSessionItem.word_id)
            .where(LearningSessionItem.learning_session_id == learning_session_id)
            .order_by(LearningSessionItem.position.asc())
        )
        return list(result.all())

    async def get_next_pending_with_word_text(
        self,
        learning_session_id: int,
    ) -> tuple[LearningSessionItem, str] | None:
        result = await self.db.execute(
            select(LearningSessionItem, Word.word_text)
            .join(Word, Word.id == LearningSessionItem.word_id)
            .where(
                LearningSessionItem.learning_session_id == learning_session_id,
                LearningSessionItem.is_done == False,  # noqa: E712
            )
            .order_by(LearningSessionItem.position.asc())
            .limit(1)
        )
        row = result.first()
        return (row[0], row[1]) if row else None

    async def count_remaining(self, learning_session_id: int) -> int:
        result = await self.db.execute(
            select(func.count(LearningSessionItem.id)).where(
                LearningSessionItem.learning_session_id == learning_session_id,
                LearningSessionItem.is_done == False,  # noqa: E712
            )
        )
        return int(result.scalar() or 0)

    async def count_summary(self, learning_session_id: int) -> tuple[int, int, int]:
        total_result = await self.db.execute(
            select(func.count(LearningSessionItem.id)).where(
                LearningSessionItem.learning_session_id == learning_session_id
            )
        )
        done_result = await self.db.execute(
            select(func.count(LearningSessionItem.id)).where(
                LearningSessionItem.learning_session_id == learning_session_id,
                LearningSessionItem.is_done == True,  # noqa: E712
            )
        )
        correct_result = await self.db.execute(
            select(func.count(LearningSessionItem.id)).where(
                LearningSessionItem.learning_session_id == learning_session_id,
                LearningSessionItem.is_done == True,  # noqa: E712
                LearningSessionItem.is_correct == True,  # noqa: E712
            )
        )
        return (
            int(total_result.scalar() or 0),
            int(done_result.scalar() or 0),
            int(correct_result.scalar() or 0),
        )

    async def list_completed_dates_for_user(self, user_id: int) -> list[date]:
        """Distinct calendar days with at least one completed learning card."""
        result = await self.db.execute(
            select(func.date(LearningSessionItem.completed_at))
            .join(
                LearningSession,
                LearningSession.id == LearningSessionItem.learning_session_id,
            )
            .where(
                LearningSession.user_id == user_id,
                LearningSessionItem.is_done == True,  # noqa: E712
                LearningSessionItem.completed_at.isnot(None),
            )
            .distinct()
        )
        return [row[0] for row in result.all() if row[0] is not None]

    async def count_completed_for_user_between(
        self,
        user_id: int,
        start: datetime,
        end: datetime,
    ) -> int:
        """Count done learning cards completed in ``[start, end)``."""
        result = await self.db.execute(
            select(func.count(LearningSessionItem.id))
            .join(
                LearningSession,
                LearningSession.id == LearningSessionItem.learning_session_id,
            )
            .where(
                LearningSession.user_id == user_id,
                LearningSessionItem.is_done == True,  # noqa: E712
                LearningSessionItem.completed_at.isnot(None),
                LearningSessionItem.completed_at >= start,
                LearningSessionItem.completed_at < end,
            )
        )
        return int(result.scalar() or 0)
