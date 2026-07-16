from __future__ import annotations

import json
import random

from app.helpers.battle.constants import BOT_ACCURACY_AI, BOT_ACCURACY_OTHER
from app.helpers.battle.text import normalize_answer
from app.models.battle import BattleMode, BattleRound


class BattleRoundAnswerHelper:
    """Slot answers, choice validation, and bot simulation for battle rounds."""

    @staticmethod
    def parse_choices(round_row: BattleRound) -> list[str]:
        if not round_row.choices_json:
            return []
        try:
            raw = json.loads(round_row.choices_json)
        except json.JSONDecodeError:
            return []
        return [str(choice) for choice in raw if str(choice).strip()]

    @staticmethod
    def choice_is_correct(selected: str, round_row: BattleRound) -> bool:
        if not selected.strip():
            return False
        choices = BattleRoundAnswerHelper.parse_choices(round_row)
        if choices:
            normalized = {normalize_answer(choice) for choice in choices}
            pick = normalize_answer(selected)
            if normalized and pick not in normalized:
                return False
        return normalize_answer(selected) == normalize_answer(round_row.correct_answer)

    @staticmethod
    def bot_choice(round_row: BattleRound, should_be_correct: bool) -> str:
        correct = round_row.correct_answer.strip()
        choices = BattleRoundAnswerHelper.parse_choices(round_row)
        if should_be_correct:
            return correct
        wrong = [
            choice
            for choice in choices
            if normalize_answer(choice) != normalize_answer(correct)
        ]
        if wrong:
            return random.choice(wrong)
        return "..."

    @staticmethod
    def bot_accuracy(mode: BattleMode) -> float:
        return BOT_ACCURACY_AI if mode == BattleMode.AI else BOT_ACCURACY_OTHER

    @staticmethod
    def bot_time_ms() -> int:
        return random.randint(1600, 8500)

    @staticmethod
    def slot_answered(round_row: BattleRound, slot: int) -> bool:
        if slot == 0:
            return round_row.player_answer is not None
        return round_row.opponent_answer is not None

    @staticmethod
    def slot_correct(round_row: BattleRound, slot: int) -> bool:
        if slot == 0:
            return bool(round_row.player_correct)
        return bool(round_row.opponent_correct)

    @staticmethod
    def write_slot_answer(
        round_row: BattleRound,
        slot: int,
        answer: str,
        correct: bool,
        time_ms: int,
    ) -> None:
        text = answer.strip()[:255]
        if slot == 0:
            round_row.player_answer = text
            round_row.player_correct = correct
            round_row.player_time_ms = time_ms
        else:
            round_row.opponent_answer = text
            round_row.opponent_correct = correct
            round_row.opponent_time_ms = time_ms

    @staticmethod
    def all_rounds_answered(rounds: list[BattleRound]) -> bool:
        return all(
            BattleRoundAnswerHelper.slot_answered(round_row, 0)
            and BattleRoundAnswerHelper.slot_answered(round_row, 1)
            for round_row in rounds
        )
