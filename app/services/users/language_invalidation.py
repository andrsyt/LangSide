"""Invalidate in-progress sessions after preferred-language change."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.repository.anti_confusion_session_repository import AntiConfusionSessionRepository
from app.repository.double_recall_session_repository import DoubleRecallSessionRepository
from app.repository.learning_session_repository import LearningSessionRepository
from app.repository.semantic_anchor_session_repository import SemanticAnchorSessionRepository
from app.repository.session_repository import SessionRepository


class UserLanguageSessionInvalidationService:
    """Drop in-progress sessions that cache old-language prompts."""

    def __init__(self, db: AsyncSession):
        self.sessions = SessionRepository(db)
        self.learning_sessions = LearningSessionRepository(db)
        self.double_recall = DoubleRecallSessionRepository(db)
        self.anti_confusion = AntiConfusionSessionRepository(db)
        self.semantic_anchor = SemanticAnchorSessionRepository(db)

    async def invalidate_for_user(self, user_id: int) -> int:
        """Delete active sessions and incomplete training exercises for the user."""
        deleted = 0
        deleted += await self.sessions.delete_active_for_user(user_id)
        deleted += await self.learning_sessions.delete_active_for_user(user_id)
        deleted += await self.double_recall.delete_unused_for_user(user_id)
        deleted += await self.anti_confusion.delete_unused_for_user(user_id)
        deleted += await self.semantic_anchor.delete_unused_for_user(user_id)
        return deleted
