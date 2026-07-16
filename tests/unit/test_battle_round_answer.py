"""Unit tests: battle answer validation and bot helpers."""

import json

from app.helpers.battle.round_answer import BattleRoundAnswerHelper
from app.models.battle import BattleRound


def _round(correct: str, choices: list[str]) -> BattleRound:
    return BattleRound(
        battle_id=1,
        round_index=0,
        prompt_text="ціна",
        correct_answer=correct,
        choices_json=json.dumps(choices),
    )


def test_choice_is_correct_exact() -> None:
    row = _round("price", ["time", "price", "water", "book"])
    assert BattleRoundAnswerHelper.choice_is_correct("price", row) is True
    assert BattleRoundAnswerHelper.choice_is_correct("water", row) is False


def test_choice_rejects_option_not_in_choices() -> None:
    row = _round("price", ["time", "water", "book", "city"])
    assert BattleRoundAnswerHelper.choice_is_correct("price", row) is False


def test_bot_choice_wrong_picks_distractor() -> None:
    row = _round("price", ["time", "price", "water", "book"])
    pick = BattleRoundAnswerHelper.bot_choice(row, should_be_correct=False)
    assert pick != "price"


def test_slot_answered_tracks_per_slot() -> None:
    row = _round("price", ["time", "price", "water", "book"])
    BattleRoundAnswerHelper.write_slot_answer(row, 0, "price", True, 1000)
    assert BattleRoundAnswerHelper.slot_answered(row, 0) is True
    assert BattleRoundAnswerHelper.slot_answered(row, 1) is False
