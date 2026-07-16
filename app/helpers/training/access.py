"""Repository-backed training and exercise session access."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.http import NotFoundError

from app.models.anti_confusion_session import AntiConfusionSession
from app.models.double_recall_session import DoubleRecallSession
from app.models.semantic_anchor_session import SemanticAnchorSession
from app.models.training import Training
from app.models.word_card import WordCard
from app.repository.anti_confusion_session_repository import (
    AntiConfusionSessionRepository,
)
from app.repository.double_recall_session_repository import (
    DoubleRecallSessionRepository,
)
from app.repository.semantic_anchor_session_repository import (
    SemanticAnchorSessionRepository,
)
from app.repository.training_repository import TrainingRepository
from app.repository.word_card_repository import WordCardRepository


class TrainingAccessService:
    """Provides repository-backed access helpers for the training domain."""

    def __init__(self, db: AsyncSession, user_id: int):
        self.user_id = user_id
        self.trainings = TrainingRepository(db)
        self.semantic_anchor_sessions = SemanticAnchorSessionRepository(db)
        self.double_recall_sessions = DoubleRecallSessionRepository(db)
        self.anti_confusion_sessions = AntiConfusionSessionRepository(db)
        self.word_cards = WordCardRepository(db)

    async def get_training(self, word_id: int) -> Training | None:
        return await self.trainings.get_by_user_and_word(self.user_id, word_id)

    async def get_or_create_training(self, word_id: int) -> Training:
        return await self.trainings.get_or_create(self.user_id, word_id)

    async def create_semantic_anchor_session(
        self,
        session: SemanticAnchorSession,
    ) -> SemanticAnchorSession:
        return await self.semantic_anchor_sessions.create(session)

    async def get_semantic_anchor_session_or_404(
        self,
        exercise_id: int,
        word_id: int,
    ) -> SemanticAnchorSession:
        session = await self.semantic_anchor_sessions.get_by_id_for_user_word(
            exercise_id,
            self.user_id,
            word_id,
        )
        if session is None:
            raise NotFoundError(
                "Invalid exercise id",
                error_code="EXERCISE_NOT_FOUND",
            )
        return session

    async def create_double_recall_session(
        self,
        session: DoubleRecallSession,
    ) -> DoubleRecallSession:
        return await self.double_recall_sessions.create(session)

    async def get_double_recall_session_or_404(
        self,
        exercise_id: int,
        word_id: int,
    ) -> DoubleRecallSession:
        session = await self.double_recall_sessions.get_by_id_for_user_word(
            exercise_id,
            self.user_id,
            word_id,
        )
        if session is None:
            raise NotFoundError(
                "Invalid exercise id",
                error_code="EXERCISE_NOT_FOUND",
            )
        return session

    async def create_anti_confusion_session(
        self,
        session: AntiConfusionSession,
    ) -> AntiConfusionSession:
        return await self.anti_confusion_sessions.create(session)

    async def get_anti_confusion_session_or_404(
        self,
        exercise_id: int,
        word_id: int,
    ) -> AntiConfusionSession:
        session = await self.anti_confusion_sessions.get_by_id_for_user_word(
            exercise_id,
            self.user_id,
            word_id,
        )
        if session is None:
            raise NotFoundError(
                "Invalid exercise id",
                error_code="EXERCISE_NOT_FOUND",
            )
        return session

    async def get_word_card(self, word_id: int) -> WordCard | None:
        return await self.word_cards.get_by_user_and_word(self.user_id, word_id)

    async def add_word_card(self, word_card: WordCard) -> WordCard:
        return await self.word_cards.add(word_card)
