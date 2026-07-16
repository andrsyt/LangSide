"""Unit tests: leaderboard response builder."""

from app.helpers.battle.leaderboard import BattleLeaderboardHelper
from app.models.battle import BattleLeague, UserBattleStats


def _stats(user_id: int, **kwargs) -> UserBattleStats:
    return UserBattleStats(
        user_id=user_id,
        rating=kwargs.get("rating", 1100),
        xp=kwargs.get("xp", 50),
        weekly_xp=kwargs.get("weekly_xp", 20),
        win_streak=kwargs.get("win_streak", 2),
        wins=kwargs.get("wins", 3),
        league=kwargs.get("league", BattleLeague.BRONZE),
    )


def test_build_entries_and_find_rank() -> None:
    rows = [
        (_stats(1), "alice"),
        (_stats(2), "bob"),
    ]
    entries = BattleLeaderboardHelper.build_entries(
        rows,
        current_user_id=2,
        xp_field="xp",
    )
    assert entries[0].rank == 1
    assert entries[1].is_you is True

    response = BattleLeaderboardHelper.response(
        scope="global",
        entries=entries,
        your_rank=BattleLeaderboardHelper.find_your_rank(entries),
    )
    assert response.scope == "global"
    assert response.your_rank == 2
