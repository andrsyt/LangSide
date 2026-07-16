"""Unit tests: english_level parsing (no database)."""

from app.helpers.english_level import (
    levels_for_user,
    parse_english_level,
)
from app.models.word import DifficultyLevel


def test_parse_cefr_codes() -> None:
    assert parse_english_level("B1") == DifficultyLevel.B1
    assert parse_english_level("b2") == DifficultyLevel.B2


def test_parse_ui_keys() -> None:
    assert parse_english_level("beginner") == DifficultyLevel.A2
    assert parse_english_level("medium") == DifficultyLevel.B1
    assert parse_english_level("advanced") == DifficultyLevel.B2


def test_parse_invalid_returns_none() -> None:
    assert parse_english_level("expert") is None
    assert parse_english_level("") is None


def test_levels_for_user_neighbors() -> None:
    assert levels_for_user(DifficultyLevel.A1) == [
        DifficultyLevel.A1,
        DifficultyLevel.A2,
    ]
    assert levels_for_user(DifficultyLevel.B1) == [
        DifficultyLevel.A2,
        DifficultyLevel.B1,
        DifficultyLevel.B2,
    ]
    assert levels_for_user(DifficultyLevel.C2) == [
        DifficultyLevel.C1,
        DifficultyLevel.C2,
    ]
