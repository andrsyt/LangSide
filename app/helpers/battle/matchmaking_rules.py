from __future__ import annotations

from app.helpers.battle.constants import (
    MATCHMAKING_CASUAL_RATING_WINDOW,
    MATCHMAKING_RANKED_RATING_WINDOW,
)
from app.schemas.battle import BattleModeRequest


def matchmaking_rating_window(mode: str | BattleModeRequest) -> int:
    mode_value = mode.value if isinstance(mode, BattleModeRequest) else mode
    if mode_value == BattleModeRequest.ranked.value:
        return MATCHMAKING_RANKED_RATING_WINDOW
    return MATCHMAKING_CASUAL_RATING_WINDOW
