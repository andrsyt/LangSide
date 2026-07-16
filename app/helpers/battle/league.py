from __future__ import annotations

from app.helpers.datetime_utils import utc_naive_now

from datetime import datetime

from app.helpers.battle.constants import LEAGUE_THRESHOLDS
from app.models.battle import BattleLeague


def season_week(dt: datetime | None = None) -> str:
    dt = dt or utc_naive_now()
    year, week, _ = dt.isocalendar()
    return f"{year}-W{week:02d}"


def league_for_rating(rating: int) -> BattleLeague:
    for threshold, league in LEAGUE_THRESHOLDS:
        if rating >= threshold:
            return league
    return BattleLeague.BRONZE


def enum_value(value: object) -> str:
    return value.value if hasattr(value, "value") else str(value)
