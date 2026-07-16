"""Unit tests: small battle and session helpers."""

from datetime import datetime, timedelta

from app.core.today_session_config import clamp_daily_goal
from app.helpers.battle.league import league_for_rating, season_week
from app.helpers.battle.matchmaking_rules import matchmaking_rating_window
from app.helpers.battle.text import normalize_answer
from app.domain.session import SessionProgressService
from app.schemas.battle import BattleModeRequest
from app.models.battle import BattleLeague


def test_normalize_answer() -> None:
    assert normalize_answer("  Price!  ") == "price"
    assert normalize_answer("TIME") == "time"


def test_league_for_rating() -> None:
    assert league_for_rating(900) == BattleLeague.BRONZE
    assert league_for_rating(1600) == BattleLeague.PLATINUM


def test_season_week_format() -> None:
    assert season_week(datetime(2026, 3, 10)) == "2026-W11"


def test_matchmaking_rating_window() -> None:
    assert matchmaking_rating_window(BattleModeRequest.ranked) == 450
    assert matchmaking_rating_window(BattleModeRequest.unranked) == 5000


def test_clamp_daily_goal() -> None:
    assert clamp_daily_goal(1) == 3
    assert clamp_daily_goal(10) == 10
    assert clamp_daily_goal(100) == 30


def test_compute_streaks_consecutive() -> None:
    today = datetime.utcnow().date()
    dates = [today - timedelta(days=i) for i in range(3)]
    current, best = SessionProgressService.compute_streaks(dates)
    assert current == 3
    assert best >= 3


def test_compute_streaks_gap_resets_current() -> None:
    today = datetime.utcnow().date()
    dates = [today - timedelta(days=5), today - timedelta(days=4)]
    current, best = SessionProgressService.compute_streaks(dates)
    assert current == 0
    assert best >= 2
