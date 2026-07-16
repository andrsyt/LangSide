"""Step-order and consumed-exercise guards for double recall."""

from __future__ import annotations

from app.core.exceptions.http import BadRequestError, GoneError
from app.models.double_recall_session import DoubleRecallSession

STEP_EN_RECALL = 0
STEP_GLOSS_RECALL = 1
STEP_SYNONYMS = 2
STEP_EXAMPLE = 3
STEP_OWN_SENTENCE = 4
TOTAL_STEPS = 5


class DoubleRecallStepGuard:
    """Validates double-recall session step state before mutations."""

    @staticmethod
    def ensure_active(session: DoubleRecallSession) -> None:
        if session.used_at is not None:
            raise GoneError(
                "Exercise already used",
                error_code="EXERCISE_ALREADY_USED",
            )

    @staticmethod
    def ensure_step(session: DoubleRecallSession, expected: int) -> None:
        if session.current_step != expected:
            raise BadRequestError(
                f"Wrong step: expected {expected}, "
                f"current_step={session.current_step}",
                error_code="WRONG_TRAINING_STEP",
            )
