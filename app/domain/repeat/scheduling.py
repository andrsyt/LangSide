"""Pure rules: spaced-repetition scheduling and study status (no I/O)."""

from __future__ import annotations

from datetime import datetime, timedelta

from app.models.word import StudyStatus
from app.helpers.datetime_utils import utc_naive_now


class RepeatSchedulingService:
    """Contains pure scheduling and status rules for spaced repetition."""

    @staticmethod
    def get_study_status(
        knowledge_level: int,
        review_count: int,
    ) -> StudyStatus:
        if knowledge_level >= 5 and review_count > 0:
            return StudyStatus.MASTERED
        return StudyStatus.LEARNING

    @staticmethod
    def calculate_next_review(
        is_correct: bool,
        correct_count: int,
        ease_factor: float,
    ) -> datetime:
        now = utc_naive_now()
        if not is_correct:
            return now + timedelta(days=1)

        if correct_count == 0:
            return now + timedelta(days=1)
        if correct_count == 1:
            return now + timedelta(days=3)
        if correct_count == 2:
            return now + timedelta(days=7)

        days = int(14 * ease_factor)
        return now + timedelta(days=days)
