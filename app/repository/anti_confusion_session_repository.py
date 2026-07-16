from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.anti_confusion_session import AntiConfusionSession


class AntiConfusionSessionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, session: AntiConfusionSession) -> AntiConfusionSession:
        self.db.add(session)
        await self.db.flush()
        return session

    async def get_by_id_for_user_word(
        self,
        exercise_id: int,
        user_id: int,
        word_id: int,
    ) -> AntiConfusionSession | None:
        result = await self.db.execute(
            select(AntiConfusionSession).where(
                AntiConfusionSession.id == exercise_id,
                AntiConfusionSession.user_id == user_id,
                AntiConfusionSession.word_id == word_id,
            )
        )
        return result.scalar_one_or_none()

    async def delete_unused_for_user(self, user_id: int) -> int:
        """Delete unused anti-confusion exercises for the user."""
        result = await self.db.execute(
            delete(AntiConfusionSession).where(
                AntiConfusionSession.user_id == user_id,
                AntiConfusionSession.used_at.is_(None),
            )
        )
        return int(result.rowcount or 0)
