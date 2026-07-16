"""Unit tests: today session pick finalization."""

from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from app.core.today_session_config import SESSION_SOURCE_DUE
from app.helpers.today_session_selection import TodaySessionWordPicker
from app.models.word import Word


def _word(word_id: int) -> Word:
    return Word(
        id=word_id,
        user_id=1,
        word_text=f"w{word_id}",
        translation="x",
    )


def _word_tr(word_id: int, word_text: str, translation: str | None) -> Word:
    return Word(
        id=word_id,
        user_id=1,
        word_text=word_text,
        translation=translation,
    )


def test_finalize_prefers_fresh_words_on_repeat() -> None:
    picks = [
        (_word(1), "learning"),
        (_word(2), "learning"),
        (_word(3), "due"),
        (_word(4), "due"),
    ]
    result = TodaySessionWordPicker._finalize_picks(
        picks,
        goal=4,
        previous_word_ids=[1, 2],
    )
    ids = [word.id for word, _ in result]
    assert ids[0] not in {1, 2}
    assert set(ids) == {3, 4, 1, 2} or ids[:2] == [3, 4]


def test_finalize_deduplicates_and_limits_goal() -> None:
    picks = [
        (_word(1), "learning"),
        (_word(1), "due"),
        (_word(2), "learning"),
    ]
    result = TodaySessionWordPicker._finalize_picks(picks, goal=2, previous_word_ids=None)
    assert len(result) == 2
    assert len({word.id for word, _ in result}) == 2


def test_today_session_skips_bad_translation() -> None:
    picks = [
        (_word_tr(1, "apple", "яблуко"), "due"),
        (_word_tr(2, "however", None), "learning"),
        (_word_tr(3, "run", "run"), "learning"),
        (_word_tr(4, "price", "я" * 81), "discovery"),
    ]

    kept, skipped = TodaySessionWordPicker._apply_quality_filter(picks)

    assert len(kept) == 1
    assert skipped == 3
    assert kept[0][0].word_text == "apple"


@pytest.mark.asyncio
async def test_today_session_picker_priority() -> None:
    word_repo = AsyncMock()
    word_repo.list_due_for_user = AsyncMock(
        return_value=[_word(1), _word(2), _word(3)],
    )
    word_repo.list_learning_words = AsyncMock(
        return_value=[_word(4), _word(5)],
    )

    picks = await TodaySessionWordPicker._pick_own_words(
        word_repo=word_repo,
        user_id=1,
        goal=3,
        now=datetime.utcnow(),
        exclude_ids=[],
        previous_word_ids=None,
    )

    assert len(picks) == 3
    assert all(source == SESSION_SOURCE_DUE for _, source in picks)
    word_repo.list_learning_words.assert_not_called()
