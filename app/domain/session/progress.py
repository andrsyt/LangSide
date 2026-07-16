"""Pure rules: word SRS updates and study streaks (no I/O)."""

from __future__ import annotations

from datetime import date

from app.domain.repeat.scheduling import RepeatSchedulingService
from app.models.word import Word
from app.helpers.datetime_utils import utc_naive_now


class SessionProgressService:
    """Contains pure progression and statistics logic for sessions."""

    @staticmethod
    def apply_review_result(word: Word, is_correct: bool) -> None:
        if word.correct_count is None:
            word.correct_count = 0
        if word.incorrect_count is None:
            word.incorrect_count = 0
        if word.review_count is None:
            word.review_count = 0
        if word.knowledge_level is None:
            word.knowledge_level = 0
        if word.ease_factor is None:
            word.ease_factor = 2.5

        if is_correct:
            word.correct_count += 1
            word.incorrect_count = 0
            if word.knowledge_level < 5:
                word.knowledge_level += 1
        else:
            word.incorrect_count += 1
            word.correct_count = 0
            word.ease_factor = max(1.3, float(word.ease_factor) - 0.2)
            word.knowledge_level = max(0, int(word.knowledge_level) - 1)

        word.next_review_at = RepeatSchedulingService.calculate_next_review(
            is_correct=is_correct,
            correct_count=int(word.correct_count),
            ease_factor=float(word.ease_factor),
        )
        word.review_count += 1
        word.last_reviewed_at = utc_naive_now()
        word.study_status = RepeatSchedulingService.get_study_status(
            int(word.knowledge_level),
            int(word.review_count),
        )

    @staticmethod
    def compute_streaks(sorted_dates: list[date]) -> tuple[int, int]:
        if not sorted_dates:
            return 0, 0

        unique_dates = sorted(set(sorted_dates))
        best = 1
        current_run = 1
        for idx in range(1, len(unique_dates)):
            if (unique_dates[idx] - unique_dates[idx - 1]).days == 1:
                current_run += 1
            else:
                best = max(best, current_run)
                current_run = 1
        best = max(best, current_run)

        today = utc_naive_now().date()
        if (today - unique_dates[-1]).days > 1:
            return 0, best

        current = 1
        for idx in range(len(unique_dates) - 1, 0, -1):
            if (unique_dates[idx] - unique_dates[idx - 1]).days == 1:
                current += 1
            else:
                break
        return current, best
