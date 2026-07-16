from __future__ import annotations

from app.helpers.datetime_utils import utc_naive_now


from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.billing.rules import BillingRulesService
from app.helpers.learning_session import (
    LearningSessionAccessService,
    LearningSessionPayloadService,
    LearningSessionSelectionService,
)
from app.domain.session import SessionProgressService
from app.models.learning_session import (
    LearningQuestType,
    LearningSession,
    LearningSessionItem,
    LearningSessionStatus,
)
from app.models.word import Word
from app.repository.learning_session_item_repository import (
    LearningSessionItemRepository,
)
from app.repository.learning_session_repository import LearningSessionRepository
from app.schemas.learning_session import (
    LearningSessionCompleteItemRequest,
    LearningSessionResponse,
)
from app.services.users.user_service import UserQueryService
from app.services.sessions.user_stats_service import UserStatsService


class LearningSessionBaseService:
    """Common dependencies for learning session use cases."""

    def __init__(self, db: AsyncSession, user_id: int):
        self.db = db
        self.user_id = user_id
        self.learning_sessions = LearningSessionRepository(db)
        self.learning_session_items = LearningSessionItemRepository(db)
        self.access = LearningSessionAccessService(db, user_id)

    async def build_response(
        self,
        learning_session: LearningSession,
    ) -> LearningSessionResponse:
        return LearningSessionResponse(
            session_id=learning_session.id,
            session_date=learning_session.session_date,
            goal=learning_session.goal,
            status=learning_session.status.value,
            items=await self.access.load_item_views(learning_session.id),
        )


class LearningSessionQueryService(LearningSessionBaseService):
    """Read-only use cases for learning sessions."""

    async def get_current_learning_session(self) -> LearningSessionResponse | None:
        learning_session = await self.learning_sessions.get_current_active_for_user(
            self.user_id
        )
        if learning_session is None:
            return None
        return await self.build_response(learning_session)

    async def get_learning_session(self, session_id: int) -> LearningSessionResponse:
        learning_session = await self.access.get_learning_session_or_404(session_id)
        return await self.build_response(learning_session)


class LearningSessionCommandService(LearningSessionBaseService):
    """Write use cases for learning sessions."""

    def __init__(self, db: AsyncSession, user_id: int):
        super().__init__(db, user_id)
        self.selection = LearningSessionSelectionService(db, user_id)
        self.user_query = UserQueryService(db)
        self.billing_rules = BillingRulesService()
        self.stats = UserStatsService(db, user_id)

    @staticmethod
    def append_items(
        items: list[LearningSessionItem],
        words: list[Word],
        learning_session_id: int,
        start_position: int,
        quest_type: LearningQuestType,
        source_bucket: str,
        exclude_ids: list[int],
    ) -> int:
        position = start_position
        for word in words:
            items.append(
                LearningSessionItem(
                    learning_session_id=learning_session_id,
                    word_id=word.id,
                    position=position,
                    quest_type=quest_type,
                    source_bucket=source_bucket,
                )
            )
            exclude_ids.append(word.id)
            position += 1
        return position

    async def start_learning_session(
        self,
        goal: int = 10,
        semantic_anchor_target: int = 3,
        double_recall_target: int = 4,
        anti_confusion_target: int = 2,
        association_recall_target: int = 1,
    ) -> LearningSessionResponse:
        user = await self.user_query.get_user_by_id(self.user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        self.billing_rules.ensure_can_start_mixed_practice(user=user)

        learning_session = await self.learning_sessions.create(
            LearningSession(
                user_id=self.user_id,
                session_date=utc_naive_now().date(),
                goal=goal,
                status=LearningSessionStatus.ACTIVE,
            )
        )

        exclude_ids: list[int] = []
        position = 1
        items: list[LearningSessionItem] = []

        semantic_words = await self.selection.pick_new_words(
            semantic_anchor_target,
            exclude_ids,
        )
        position = self.append_items(
            items,
            semantic_words,
            learning_session.id,
            position,
            LearningQuestType.SEMANTIC_ANCHOR,
            "new",
            exclude_ids,
        )

        due_words = await self.selection.pick_due_words(
            double_recall_target,
            exclude_ids,
        )
        position = self.append_items(
            items,
            due_words,
            learning_session.id,
            position,
            LearningQuestType.DOUBLE_RECALL,
            "due",
            exclude_ids,
        )

        confusion_words = await self.selection.pick_confusion_words(
            anti_confusion_target,
            exclude_ids,
        )
        position = self.append_items(
            items,
            confusion_words,
            learning_session.id,
            position,
            LearningQuestType.ANTI_CONFUSION,
            "confusion",
            exclude_ids,
        )

        association_words = await self.selection.pick_association_recall_words(
            association_recall_target,
            exclude_ids,
        )
        self.append_items(
            items,
            association_words,
            learning_session.id,
            position,
            LearningQuestType.ASSOCIATION_RECALL,
            "association",
            exclude_ids,
        )

        if not items:
            fallback_limit = max(
                goal,
                semantic_anchor_target
                + double_recall_target
                + anti_confusion_target
                + association_recall_target,
                1,
            )
            fallback_words = await self.selection.pick_any_learning_words(
                fallback_limit,
                exclude_ids,
            )
            if not fallback_words:
                raise HTTPException(
                    status_code=400,
                    detail="No eligible words found for a mixed learning session",
                )
            position = self.append_items(
                items,
                fallback_words,
                learning_session.id,
                position,
                LearningQuestType.DOUBLE_RECALL,
                "fallback",
                exclude_ids,
            )

        learning_session.goal = len(items)
        await self.learning_session_items.create_many(items)
        await self.db.commit()
        await self.db.refresh(learning_session)
        return await self.build_response(learning_session)

    async def complete_learning_session_item(
        self,
        session_id: int,
        item_id: int,
        payload: LearningSessionCompleteItemRequest,
    ) -> tuple[LearningSessionItem, Word, int]:
        learning_session = await self.access.get_learning_session_or_404(session_id)
        if learning_session.status == LearningSessionStatus.FINISHED:
            raise HTTPException(
                status_code=400,
                detail="Learning session already finished",
            )

        item = await self.access.get_session_item_or_404(session_id, item_id)
        if item.is_done:
            raise HTTPException(
                status_code=400,
                detail="Learning session item already completed",
            )

        derived_correct = LearningSessionPayloadService.derive_correct(
            item.quest_type,
            payload,
        )
        if derived_correct is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Completion requires either explicit correct flag or compatible result_payload",
            )

        word = await self.access.get_word_or_404(item.word_id)
        SessionProgressService.apply_review_result(word, derived_correct)
        item.is_done = True
        item.is_correct = derived_correct
        item.result_payload = payload.result_payload
        item.completed_at = utc_naive_now()

        remaining_after = await self.learning_session_items.count_remaining(session_id)
        if remaining_after == 0:
            learning_session.status = LearningSessionStatus.FINISHED
            learning_session.finished_at = utc_naive_now()

        await self.stats.record_exercise_completed()
        await self.db.commit()
        await self.db.refresh(word)
        return item, word, remaining_after

    async def finish_learning_session(self, session_id: int) -> dict:
        learning_session = await self.access.get_learning_session_or_404(session_id)
        total, done, correct = await self.learning_session_items.count_summary(
            session_id
        )

        learning_session.status = LearningSessionStatus.FINISHED
        learning_session.finished_at = utc_naive_now()
        await self.db.commit()
        return {
            "session_id": session_id,
            "total": total,
            "done": done,
            "correct": correct,
            "incorrect": max(0, done - correct),
            "finished": True,
        }
