from datetime import date

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.learning_session import LearningSession, LearningSessionStatus


class LearningSessionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, learning_session: LearningSession) -> LearningSession:
        self.db.add(learning_session)
        await self.db.flush()
        return learning_session

    async def get_by_id_for_user(
        self,
        session_id: int,
        user_id: int,
    ) -> LearningSession | None:
        result = await self.db.execute(
            select(LearningSession).where(
                LearningSession.id == session_id,
                LearningSession.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_current_active_for_user(self, user_id: int) -> LearningSession | None:
        result = await self.db.execute(
            select(LearningSession)
            .where(
                LearningSession.user_id == user_id,
                LearningSession.status == LearningSessionStatus.ACTIVE,
            )
            .order_by(LearningSession.id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_finished_dates_for_user(self, user_id: int) -> list[date]:
        result = await self.db.execute(
            select(func.date(LearningSession.finished_at))
            .where(
                LearningSession.user_id == user_id,
                LearningSession.status == LearningSessionStatus.FINISHED,
                LearningSession.finished_at.isnot(None),
            )
            .distinct()
            .order_by(func.date(LearningSession.finished_at).asc())
        )
        return [row[0] for row in result.all() if row[0] is not None]

    async def delete_active_for_user(self, user_id: int) -> int:
        """Delete active learning sessions for the user. Returns deleted row count."""
        result = await self.db.execute(
            delete(LearningSession).where(
                LearningSession.user_id == user_id,
                LearningSession.status == LearningSessionStatus.ACTIVE,
            )
        )
        return int(result.rowcount or 0)
