"""Server-side round deadlines and stale battle cleanup."""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import timedelta

from app.helpers.battle.constants import (
    BATTLE_TIMEOUT_ANSWER,
    BATTLE_TIMEOUT_TIME_MS,
    ROUND_SECONDS,
)
from app.helpers.battle.finish import BattleFinishHelper
from app.helpers.battle.round_answer import BattleRoundAnswerHelper
from app.helpers.datetime_utils import utc_naive_now
from app.models.battle import (
    Battle,
    BattleParticipant,
    BattleRound,
    BattleStatus,
    UserBattleStats,
)
from app.schemas.battle import BattleFinishResponse


@dataclass
class BattleTimeoutResult:
    changed: bool = False
    finished: BattleFinishResponse | None = None


class BattleTimeoutHelper:
    """Enforces per-round deadlines and applies score updates."""

    @staticmethod
    def current_round(rounds: list[BattleRound]) -> BattleRound | None:
        for row in sorted(rounds, key=lambda item: item.round_index):
            if not (
                BattleRoundAnswerHelper.slot_answered(row, 0)
                and BattleRoundAnswerHelper.slot_answered(row, 1)
            ):
                return row
        return None

    @staticmethod
    def ensure_deadline(battle: Battle) -> None:
        if battle.round_deadline_at is None:
            battle.round_deadline_at = utc_naive_now() + timedelta(seconds=battle.round_seconds)

    @staticmethod
    def _apply_round_scores(
        round_row: BattleRound,
        me: BattleParticipant,
        opponent: BattleParticipant,
    ) -> None:
        my_slot = me.slot
        if BattleRoundAnswerHelper.slot_correct(round_row, my_slot):
            me.score += 1
        if BattleRoundAnswerHelper.slot_correct(round_row, opponent.slot):
            opponent.score += 1

    @staticmethod
    def _timeout_slot(
        battle: Battle,
        round_row: BattleRound,
        slot: int,
        me: BattleParticipant,
        opponent: BattleParticipant,
    ) -> None:
        if BattleRoundAnswerHelper.slot_answered(round_row, slot):
            return
        occupant = me if slot == me.slot else opponent
        if occupant.is_bot:
            accuracy = BattleRoundAnswerHelper.bot_accuracy(battle.mode)
            correct = random.random() < accuracy
            answer = BattleRoundAnswerHelper.bot_choice(round_row, correct)
            BattleRoundAnswerHelper.write_slot_answer(
                round_row,
                slot,
                answer,
                correct,
                BattleRoundAnswerHelper.bot_time_ms(),
            )
            return

        BattleRoundAnswerHelper.write_slot_answer(
            round_row,
            slot,
            BATTLE_TIMEOUT_ANSWER,
            False,
            BATTLE_TIMEOUT_TIME_MS,
        )

    @classmethod
    def resolve(
        cls,
        battle: Battle,
        me: BattleParticipant,
        opponent: BattleParticipant,
        stats: UserBattleStats,
    ) -> BattleTimeoutResult:
        if battle.status != BattleStatus.ACTIVE:
            return BattleTimeoutResult()

        cls.ensure_deadline(battle)
        result = BattleTimeoutResult()
        now = utc_naive_now()

        while battle.status == BattleStatus.ACTIVE:
            round_row = cls.current_round(battle.rounds)
            if round_row is None:
                finish = BattleFinishHelper.apply(battle, me, opponent, stats)
                return BattleTimeoutResult(changed=True, finished=finish)

            if battle.round_deadline_at is None or now < battle.round_deadline_at:
                break

            cls._timeout_slot(battle, round_row, 0, me, opponent)
            cls._timeout_slot(battle, round_row, 1, me, opponent)
            cls._apply_round_scores(round_row, me, opponent)
            result.changed = True

            if cls.current_round(battle.rounds) is None:
                finish = BattleFinishHelper.apply(battle, me, opponent, stats)
                result.finished = finish
                break

            battle.round_deadline_at = now + timedelta(seconds=battle.round_seconds)

        return result

    @staticmethod
    def start_next_round_deadline(battle: Battle) -> None:
        battle.round_deadline_at = utc_naive_now() + timedelta(
            seconds=battle.round_seconds or ROUND_SECONDS
        )
