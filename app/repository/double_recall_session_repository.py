from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.double_recall_session import DoubleRecallSession


class DoubleRecallSessionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, session: DoubleRecallSession) -> DoubleRecallSession:
        self.db.add(session)
        await self.db.flush()
        return session

    async def get_by_id_for_user_word(
        self,
        exercise_id: int,
        user_id: int,
        word_id: int,
    ) -> DoubleRecallSession | None:
        result = await self.db.execute(
            select(DoubleRecallSession).where(
                DoubleRecallSession.id == exercise_id,
                DoubleRecallSession.user_id == user_id,
                DoubleRecallSession.word_id == word_id,
            )
        )
        return result.scalar_one_or_none()

    async def delete_unused_for_user(self, user_id: int) -> int:
        """Delete unused double-recall exercises for the user."""
        result = await self.db.execute(
            delete(DoubleRecallSession).where(
                DoubleRecallSession.user_id == user_id,
                DoubleRecallSession.used_at.is_(None),
            )
        )
        return int(result.rowcount or 0)
