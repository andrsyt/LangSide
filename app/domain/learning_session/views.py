"""Pure mapping: learning-session items → API views (no I/O)."""

from __future__ import annotations

from app.models.learning_session import LearningQuestType, LearningSessionItem
from app.schemas.learning_session import LearningSessionItemView


class LearningSessionViewService:
    """Builds API views for learning sessions."""

    @staticmethod
    def launch_path(quest_type: LearningQuestType, word_id: int) -> str:
        if quest_type == LearningQuestType.SEMANTIC_ANCHOR:
            return f"/training/word/{word_id}/exercise/semantic-anchor"
        if quest_type == LearningQuestType.DOUBLE_RECALL:
            return f"/training/word/{word_id}/exercise/double-recall"
        if quest_type == LearningQuestType.ANTI_CONFUSION:
            return f"/training/word/{word_id}/exercise/anti-confusion"
        return f"/training/word/{word_id}/exercise/association-recall"

    @classmethod
    def item_to_view(
        cls,
        item: LearningSessionItem,
        word_text: str,
    ) -> LearningSessionItemView:
        return LearningSessionItemView(
            item_id=item.id,
            word_id=item.word_id,
            word_text=word_text,
            quest_type=item.quest_type.value,
            source_bucket=item.source_bucket,
            position=item.position,
            is_done=item.is_done,
            is_correct=item.is_correct,
            launch_path=cls.launch_path(item.quest_type, item.word_id),
        )
