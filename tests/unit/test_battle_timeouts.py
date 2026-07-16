"""Unit tests: battle round deadline resolution."""

from datetime import timedelta

from app.helpers.battle.timeouts import BattleTimeoutHelper
from app.helpers.datetime_utils import utc_naive_now
from app.models.battle import (
    Battle,
    BattleMode,
    BattleParticipant,
    BattleRound,
    BattleStatus,
    UserBattleStats,
)


def _active_battle(*, deadline_passed: bool) -> Battle:
    now = utc_naive_now()
    deadline = now - timedelta(seconds=1) if deadline_passed else now + timedelta(seconds=30)
    battle = Battle(
        id=1,
        mode=BattleMode.AI,
        status=BattleStatus.ACTIVE,
        is_ranked=False,
        round_count=1,
        round_seconds=15,
        round_deadline_at=deadline,
    )
    battle.rounds = [
        BattleRound(
            battle_id=1,
            round_index=0,
            prompt_text="ціна",
            correct_answer="price",
            choices_json='["time","price","water","book"]',
        )
    ]
    battle.participants = []
    return battle


def test_current_round_first_unfinished() -> None:
    battle = _active_battle(deadline_passed=False)
    row = BattleTimeoutHelper.current_round(battle.rounds)
    assert row is not None
    assert row.round_index == 0


def test_resolve_fills_unanswered_on_deadline() -> None:
    battle = _active_battle(deadline_passed=True)
    me = BattleParticipant(
        battle_id=1,
        user_id=10,
        slot=0,
        display_name="Me",
        is_bot=False,
        score=0,
    )
    bot = BattleParticipant(
        battle_id=1,
        user_id=None,
        slot=1,
        display_name="AI",
        is_bot=True,
        score=0,
    )
    stats = UserBattleStats(
        user_id=10,
        rating=1000,
        xp=0,
        wins=0,
        losses=0,
        draws=0,
        win_streak=0,
        best_win_streak=0,
        battles_played=0,
        weekly_xp=0,
    )

    result = BattleTimeoutHelper.resolve(battle, me, bot, stats)

    assert result.changed is True
    assert BattleTimeoutHelper.current_round(battle.rounds) is None
    assert battle.rounds[0].player_answer is not None
    assert battle.rounds[0].opponent_answer is not None
