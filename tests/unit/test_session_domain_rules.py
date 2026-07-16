"""Unit tests: pure domain rules (repeat answers, SRS, streaks, payloads)."""

from datetime import date, timedelta
from unittest.mock import MagicMock

from app.domain.learning_session import LearningSessionPayloadService
from app.domain.repeat import RepeatAnswerService, RepeatSchedulingService
from app.domain.session import SessionProgressService
from app.models.learning_session import LearningQuestType
from app.models.word import StudyStatus
from app.schemas.learning_session import LearningSessionCompleteItemRequest


def test_repeat_answer_exact_match() -> None:
    assert RepeatAnswerService.check_translation_correctness("яблуко", "яблуко")


def test_repeat_answer_rejects_empty_primary() -> None:
    assert not RepeatAnswerService.check_translation_correctness("apple", None)


def test_repeat_scheduling_mastered_status() -> None:
    assert (
        RepeatSchedulingService.get_study_status(knowledge_level=5, review_count=1)
        == StudyStatus.MASTERED
    )
    assert (
        RepeatSchedulingService.get_study_status(knowledge_level=4, review_count=10)
        == StudyStatus.LEARNING
    )


def test_compute_streaks_empty() -> None:
    assert SessionProgressService.compute_streaks([]) == (0, 0)


def test_compute_streaks_consecutive_including_today() -> None:
    today = date.today()
    dates = [today - timedelta(days=2), today - timedelta(days=1), today]
    current, best = SessionProgressService.compute_streaks(dates)
    assert current == 3
    assert best == 3


def test_compute_streaks_broken_current() -> None:
    today = date.today()
    dates = [today - timedelta(days=5), today - timedelta(days=4)]
    current, best = SessionProgressService.compute_streaks(dates)
    assert current == 0
    assert best == 2


def test_payload_prefers_explicit_correct() -> None:
    payload = LearningSessionCompleteItemRequest(
        correct=True,
        result_payload={"overall_correct": False},
    )
    assert (
        LearningSessionPayloadService.derive_correct(
            LearningQuestType.DOUBLE_RECALL,
            payload,
        )
        is True
    )


def test_payload_reads_quest_specific_key() -> None:
    payload = LearningSessionCompleteItemRequest(
        result_payload={"is_context_correct": True},
    )
    assert (
        LearningSessionPayloadService.derive_correct(
            LearningQuestType.SEMANTIC_ANCHOR,
            payload,
        )
        is True
    )


def test_apply_review_result_increments_on_correct() -> None:
    word = MagicMock()
    word.correct_count = 0
    word.incorrect_count = 0
    word.review_count = 0
    word.knowledge_level = 0
    word.ease_factor = 2.5
    word.next_review_at = None
    word.last_reviewed_at = None
    word.study_status = StudyStatus.LEARNING

    SessionProgressService.apply_review_result(word, is_correct=True)

    assert word.correct_count == 1
    assert word.knowledge_level == 1
    assert word.review_count == 1
