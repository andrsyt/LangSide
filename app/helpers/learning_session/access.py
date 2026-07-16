"""404-safe access helpers for learning session entities."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.http import NotFoundError
from app.domain.learning_session.views import LearningSessionViewService
from app.helpers.word_helpers import WordAccessService
from app.models.learning_session import LearningSession, LearningSessionItem
from app.models.word import Word
from app.repository.learning_session_item_repository import (
    LearningSessionItemRepository,
)
from app.repository.learning_session_repository import LearningSessionRepository
from app.schemas.learning_session import LearningSessionItemView


class LearningSessionAccessService:
    """Provides 404-safe access helpers for learning session entities."""

    def __init__(self, db: AsyncSession, user_id: int):
        self.user_id = user_id
        self.learning_sessions = LearningSessionRepository(db)
        self.learning_session_items = LearningSessionItemRepository(db)
        self._words = WordAccessService(db, user_id)

    async def get_learning_session_or_404(self, session_id: int) -> LearningSession:
        learning_session = await self.learning_sessions.get_by_id_for_user(
            session_id,
            self.user_id,
        )
        if learning_session is None:
            raise NotFoundError(
                "Learning session not found",
                error_code="LEARNING_SESSION_NOT_FOUND",
            )
        return learning_session

    async def get_session_item_or_404(
        self,
        session_id: int,
        item_id: int,
    ) -> LearningSessionItem:
        item = await self.learning_session_items.get_by_id_in_session(session_id, item_id)
        if item is None:
            raise NotFoundError(
                "Learning session item not found",
                error_code="LEARNING_SESSION_ITEM_NOT_FOUND",
            )
        return item

    async def get_word_or_404(self, word_id: int) -> Word:
        return await self._words.get_word_or_404(word_id)

    async def load_item_views(
        self,
        learning_session_id: int,
    ) -> list[LearningSessionItemView]:
        rows = await self.learning_session_items.list_with_word_text(learning_session_id)
        return [
            LearningSessionViewService.item_to_view(item, word_text)
            for item, word_text in rows
        ]
