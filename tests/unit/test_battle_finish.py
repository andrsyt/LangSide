"""Unit tests: ELO delta and XP rules."""

from app.helpers.battle.finish import BattleFinishHelper
from app.models.battle import BattleParticipant


def test_rating_delta_ranked_win() -> None:
    delta = BattleFinishHelper.rating_delta(
        is_ranked=True,
        won=True,
        opponent_is_bot=False,
        rating_before=1000,
        opponent_rating_before=1200,
    )
    assert delta >= 8


def test_rating_delta_not_ranked_is_zero() -> None:
    delta = BattleFinishHelper.rating_delta(
        is_ranked=False,
        won=True,
        opponent_is_bot=False,
        rating_before=1000,
        opponent_rating_before=1200,
    )
    assert delta == 0


def test_rating_delta_vs_bot_is_zero() -> None:
    delta = BattleFinishHelper.rating_delta(
        is_ranked=True,
        won=True,
        opponent_is_bot=True,
        rating_before=1000,
        opponent_rating_before=900,
    )
    assert delta == 0


def test_xp_win_vs_bot() -> None:
    xp = BattleFinishHelper.xp_for_outcome(
        your_score=5,
        won=True,
        opponent_is_bot=True,
    )
    assert xp == 5 * 15 + 35


def test_resolve_outcome() -> None:
    you = BattleParticipant(
        battle_id=1, slot=0, display_name="A", score=3
    )
    opp = BattleParticipant(
        battle_id=1, slot=1, display_name="B", score=1
    )
    outcome = BattleFinishHelper.resolve_outcome(you, opp)
    assert outcome.won is True
    assert outcome.is_draw is False
