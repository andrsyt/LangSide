"""Unit tests: matchmaking search copy."""

from app.helpers.battle.constants import MATCHMAKING_AI_SECONDS
from app.helpers.battle.matchmaking_messages import matchmaking_search_message


def test_matchmaking_messages_by_elapsed() -> None:
    assert "Scanning" in matchmaking_search_message(0.5)
    assert "skill" in matchmaking_search_message(3)
    assert "Almost" in matchmaking_search_message(MATCHMAKING_AI_SECONDS - 1)
    assert "AI is ready" in matchmaking_search_message(MATCHMAKING_AI_SECONDS + 1)
