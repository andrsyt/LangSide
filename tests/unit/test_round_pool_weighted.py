"""Unit tests: battle round pool weighted sampling (no DB)."""

from app.helpers.battle.round_pool import BattleRoundPoolBuilder
from app.models.word import DifficultyLevel


def test_weighted_sample_unique_respects_count() -> None:
    builder = BattleRoundPoolBuilder(db=None)  # type: ignore[arg-type]
    rows = [
        ("easy", DifficultyLevel.A1),
        ("mid", DifficultyLevel.B1),
        ("hard", DifficultyLevel.C2),
        ("extra", DifficultyLevel.A2),
    ]
    picked = builder._weighted_sample_unique(rows, 2)
    assert len(picked) == 2
    assert len({item["answer"] for item in picked}) == 2


def test_make_choices_includes_correct() -> None:
    pool = [{"answer": "price"}, {"answer": "time"}, {"answer": "water"}]
    choices = BattleRoundPoolBuilder._make_choices("price", pool)
    assert "price" in choices
    assert len(choices) == 4
