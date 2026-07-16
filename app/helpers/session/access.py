"""404-safe access helpers for the today-session domain."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.http import NotFoundError
from app.helpers.word_helpers import WordAccessService
from app.models.session import Session, SessionItem
from app.models.word import Word
from app.repository.session_item_repository import SessionItemRepository
from app.repository.session_repository import SessionRepository
from app.repository.word_repository import WordRepository


class SessionAccessService:
    """Provides 404-safe access helpers for the session domain."""

    def __init__(self, db: AsyncSession, user_id: int):
        self.user_id = user_id
        self.sessions = SessionRepository(db)
        self.session_items = SessionItemRepository(db)
        self._word_access = WordAccessService(db, user_id)
        self.word_repo = WordRepository(db)

    async def get_session_or_404(self, session_id: int) -> Session:
        session = await self.sessions.get_by_id_for_user(session_id, self.user_id)
        if session is None:
            raise NotFoundError("Session not found", error_code="SESSION_NOT_FOUND")
        return session

    async def get_word_or_404(self, word_id: int) -> Word:
        return await self._word_access.get_word_or_404(word_id)

    async def get_session_item_or_404(
        self,
        session_id: int,
        word_id: int,
    ) -> SessionItem:
        item = await self.session_items.get_by_session_and_word(session_id, word_id)
        if item is None:
            raise NotFoundError(
                "Session item not found",
                error_code="SESSION_ITEM_NOT_FOUND",
            )
        return item

    async def load_session_words(self, session_id: int) -> list[Word]:
        items = await self.session_items.list_for_session(session_id)
        if not items:
            return []
        word_ids = [item.word_id for item in items]
        words = await self.word_repo.list_by_ids_for_user(self.user_id, word_ids)
        words_by_id = {word.id: word for word in words}
        return [words_by_id[word_id] for word_id in word_ids if word_id in words_by_id]

    async def reset_session_items(self, session_id: int) -> None:
        await self.session_items.reset_for_session(session_id)

    async def reshuffle_session_item_positions(self, session_id: int) -> None:
        await self.session_items.reshuffle_positions(session_id)
