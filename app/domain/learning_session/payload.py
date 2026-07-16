"""Pure rules: interpret learning-session completion payloads (no I/O)."""

from __future__ import annotations

from app.models.learning_session import LearningQuestType
from app.schemas.learning_session import LearningSessionCompleteItemRequest


class LearningSessionPayloadService:
    """Contains payload interpretation rules for learning session completion."""

    @staticmethod
    def derive_correct(
        quest_type: LearningQuestType,
        payload: LearningSessionCompleteItemRequest,
    ) -> bool | None:
        if payload.correct is not None:
            return payload.correct

        result_payload = payload.result_payload or {}
        if quest_type == LearningQuestType.SEMANTIC_ANCHOR:
            value = result_payload.get("is_context_correct")
        elif quest_type == LearningQuestType.DOUBLE_RECALL:
            value = result_payload.get("overall_correct")
        elif quest_type == LearningQuestType.ANTI_CONFUSION:
            value = result_payload.get("is_correct")
        else:
            value = result_payload.get("correct")

        if value is None:
            return None
        return bool(value)
