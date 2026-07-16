from __future__ import annotations

from app.helpers.datetime_utils import utc_naive_now

from dataclasses import dataclass

from app.helpers.battle.constants import DEFAULT_RATING, ELO_K, MIN_RATING
from app.helpers.battle.league import league_for_rating
from app.models.battle import Battle, BattleParticipant, BattleStatus, UserBattleStats
from app.schemas.battle import BattleFinishResponse


@dataclass(frozen=True)
class BattleOutcome:
    won: bool | None
    is_draw: bool


class BattleFinishHelper:
    """Applies battle results to stats and builds the finish API payload."""

    @staticmethod
    def resolve_outcome(you: BattleParticipant, opponent: BattleParticipant) -> BattleOutcome:
        if you.score > opponent.score:
            return BattleOutcome(won=True, is_draw=False)
        if you.score < opponent.score:
            return BattleOutcome(won=False, is_draw=False)
        return BattleOutcome(won=None, is_draw=True)

    @staticmethod
    def rating_delta(
        *,
        is_ranked: bool,
        won: bool | None,
        opponent_is_bot: bool,
        rating_before: int,
        opponent_rating_before: int | None,
    ) -> int:
        if not is_ranked or won is None or opponent_is_bot:
            return 0
        expected = 1 / (
            1 + 10 ** ((opponent_rating_before or DEFAULT_RATING) - rating_before) / 400
        )
        score = 1.0 if won else 0.0
        return int(round(ELO_K * (score - expected)))

    @staticmethod
    def xp_for_outcome(
        *,
        your_score: int,
        won: bool | None,
        opponent_is_bot: bool,
    ) -> int:
        base_xp = 15 * your_score
        if won:
            return base_xp + (35 if opponent_is_bot else 45)
        if won is None:
            return base_xp + 12
        return base_xp + 8

    @staticmethod
    def apply(
        battle: Battle,
        you: BattleParticipant,
        opponent: BattleParticipant,
        stats: UserBattleStats,
    ) -> BattleFinishResponse:
        outcome = BattleFinishHelper.resolve_outcome(you, opponent)
        battle.status = BattleStatus.FINISHED
        battle.finished_at = utc_naive_now()

        rating_before = stats.rating
        delta = BattleFinishHelper.rating_delta(
            is_ranked=battle.is_ranked,
            won=outcome.won,
            opponent_is_bot=opponent.is_bot,
            rating_before=rating_before,
            opponent_rating_before=opponent.rating_before,
        )
        stats.rating = max(MIN_RATING, rating_before + delta)

        xp = BattleFinishHelper.xp_for_outcome(
            your_score=you.score,
            won=outcome.won,
            opponent_is_bot=opponent.is_bot,
        )
        stats.xp += xp
        stats.weekly_xp += xp
        stats.battles_played += 1

        if outcome.won:
            stats.wins += 1
            stats.win_streak += 1
            stats.best_win_streak = max(stats.best_win_streak, stats.win_streak)
            headline = "Victory!"
            subline = f"You beat {opponent.display_name}"
        elif outcome.is_draw:
            stats.draws += 1
            stats.win_streak = 0
            headline = "Draw"
            subline = "Even match — rematch?"
        else:
            stats.losses += 1
            stats.win_streak = 0
            headline = "Defeat"
            subline = f"{opponent.display_name} won this duel"

        stats.league = league_for_rating(stats.rating)
        you.is_winner = outcome.won
        you.xp_earned = xp
        you.rating_after = stats.rating
        opponent.is_winner = False if outcome.won else (True if outcome.won is False else None)

        return BattleFinishResponse(
            battle_id=battle.id,
            won=outcome.won,
            is_draw=outcome.is_draw,
            your_score=you.score,
            opponent_score=opponent.score,
            xp_earned=xp,
            rating_before=rating_before,
            rating_after=stats.rating,
            rating_delta=delta,
            win_streak=stats.win_streak,
            headline=headline,
            subline=subline,
        )
