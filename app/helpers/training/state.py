"""Training quest-type completion state on Training rows."""

from __future__ import annotations

from app.models.training import Training


class TrainingStateHelper:
    """Helper methods for training state."""

    @staticmethod
    def append_completed_quest_type(training: Training, quest_type: str) -> None:
        current = list(training.completed_quest_types or [])
        if quest_type not in current:
            current.append(quest_type)
        training.completed_quest_types = current

    _append_completed_quest_type = append_completed_quest_type
