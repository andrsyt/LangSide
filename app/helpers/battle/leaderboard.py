from __future__ import annotations

from app.helpers.battle.league import enum_value, season_week
from app.models.battle import UserBattleStats
from app.schemas.battle import LeaderboardEntry, LeaderboardResponse


class BattleLeaderboardHelper:
    @staticmethod
    def build_entries(
        rows: list[tuple[UserBattleStats, str]],
        *,
        current_user_id: int,
        xp_field: str = "xp",
    ) -> list[LeaderboardEntry]:
        return [
            LeaderboardEntry(
                rank=index + 1,
                user_id=stats.user_id,
                username=username,
                rating=stats.rating,
                xp=(
                    stats.weekly_xp
                    if xp_field == "weekly_xp"
                    else stats.win_streak
                    if xp_field == "win_streak"
                    else stats.xp
                ),
                wins=stats.wins,
                win_streak=stats.win_streak,
                league=enum_value(stats.league),
                is_you=stats.user_id == current_user_id,
            )
            for index, (stats, username) in enumerate(rows)
        ]

    @staticmethod
    def response(
        *,
        scope: str,
        entries: list[LeaderboardEntry],
        your_rank: int | None,
        order_weekly: bool = False,
    ) -> LeaderboardResponse:
        return LeaderboardResponse(
            scope=scope,
            season_week=season_week() if order_weekly else None,
            your_rank=your_rank,
            entries=entries,
        )

    @staticmethod
    def find_your_rank(entries: list[LeaderboardEntry]) -> int | None:
        for entry in entries:
            if entry.is_you:
                return entry.rank
        return None
