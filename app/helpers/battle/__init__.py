"""Battle helpers split by concern; use `app.helpers.battle` or `battle_helpers` shim."""

from .constants import (
    AI_OPPONENT_NAME,
    BATTLE_STALE_HOURS,
    CHOICES_PER_ROUND,
    MATCHMAKING_AI_SECONDS,
    MATCHMAKING_CASUAL_RATING_WINDOW,
    MATCHMAKING_RANKED_RATING_WINDOW,
    MATCHMAKING_SEARCH_MAX_AGE_SECONDS,
    ROUND_SECONDS,
)
from .timeouts import BattleTimeoutHelper
from .eligibility import non_test_user_sql_conditions
from .finish import BattleFinishHelper
from .leaderboard import BattleLeaderboardHelper
from .league import enum_value, league_for_rating, season_week
from .matchmaking_messages import matchmaking_search_message
from .prompts import battle_prompt_for_word
from .round_answer import BattleRoundAnswerHelper
from .round_pool import BattleRoundPoolBuilder
from .setup import BattleSetupHelper
from .state import BattleStateMapper
from .text import normalize_answer
from .users import is_eligible_battle_user, public_display_name

__all__ = [
    "AI_OPPONENT_NAME",
    "CHOICES_PER_ROUND",
    "MATCHMAKING_AI_SECONDS",
    "MATCHMAKING_CASUAL_RATING_WINDOW",
    "MATCHMAKING_RANKED_RATING_WINDOW",
    "MATCHMAKING_SEARCH_MAX_AGE_SECONDS",
    "battle_prompt_for_word",
    "ROUND_SECONDS",
    "BattleFinishHelper",
    "BattleLeaderboardHelper",
    "BattleRoundAnswerHelper",
    "BattleRoundPoolBuilder",
    "BattleSetupHelper",
    "BattleStateMapper",
    "BattleTimeoutHelper",
    "BATTLE_STALE_HOURS",
    "enum_value",
    "is_eligible_battle_user",
    "league_for_rating",
    "matchmaking_search_message",
    "non_test_user_sql_conditions",
    "normalize_answer",
    "public_display_name",
    "season_week",
]
