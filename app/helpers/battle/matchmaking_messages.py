from __future__ import annotations

from app.helpers.battle.constants import MATCHMAKING_AI_SECONDS


def matchmaking_search_message(elapsed: float) -> str:
    if elapsed < 2:
        return "Scanning for players nearby..."
    if elapsed < 4:
        return "Matching by skill level..."
    if elapsed < MATCHMAKING_AI_SECONDS:
        return "Almost there — hang tight"
    return "No human opponent yet — AI is ready"
