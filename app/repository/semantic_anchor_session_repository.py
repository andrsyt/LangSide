from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.semantic_anchor_session import SemanticAnchorSession


class SemanticAnchorSessionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, session: SemanticAnchorSession) -> SemanticAnchorSession:
        self.db.add(session)
        await self.db.flush()
        return session

    async def get_by_id_for_user_word(
        self,
        exercise_id: int,
        user_id: int,
        word_id: int,
    ) -> SemanticAnchorSession | None:
        result = await self.db.execute(
            select(SemanticAnchorSession).where(
                SemanticAnchorSession.id == exercise_id,
                SemanticAnchorSession.user_id == user_id,
                SemanticAnchorSession.word_id == word_id,
            )
        )
        return result.scalar_one_or_none()

    async def delete_unused_for_user(self, user_id: int) -> int:
        """Delete unused semantic-anchor exercises for the user."""
        result = await self.db.execute(
            delete(SemanticAnchorSession).where(
                SemanticAnchorSession.user_id == user_id,
                SemanticAnchorSession.used_at.is_(None),
            )
        )
        return int(result.rowcount or 0)
