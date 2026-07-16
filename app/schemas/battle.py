from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class BattleModeRequest(str, Enum):
    quick = "quick"
    ranked = "ranked"
    unranked = "unranked"
    typing = "typing"
    voice = "voice"
    ai = "ai"


class QuickBattleStartRequest(BaseModel):
    mode: BattleModeRequest = BattleModeRequest.quick


class MatchmakingJoinRequest(BaseModel):
    mode: BattleModeRequest = BattleModeRequest.quick


class MatchmakingOpponentPreview(BaseModel):
    user_id: int
    username: str
    rating: int
    league: str
    is_bot: bool = False


class MatchmakingStatusResponse(BaseModel):
    ticket_id: int
    status: str
    elapsed_seconds: float
    can_play_ai: bool = False
    search_message: str | None = None
    opponent: MatchmakingOpponentPreview | None = None
    battle: BattleStateResponse | None = None


class BattleOpponentView(BaseModel):
    display_name: str
    is_bot: bool
    rating: int | None = None
    score: int = 0


class BattleRoundView(BaseModel):
    round_index: int
    prompt_text: str
    choices: list[str] = Field(default_factory=list)
    answered: bool = False
    player_correct: bool | None = None
    opponent_correct: bool | None = None


class BattleRoundAnswerRequest(BaseModel):
    answer: str
    time_ms: int = Field(ge=0, le=120_000)


class BattleRoundResultView(BaseModel):
    round_index: int
    player_correct: bool
    opponent_correct: bool | None = None
    correct_answer: str
    player_score: int
    opponent_score: int
    waiting_for_opponent: bool = False


class BattleStateResponse(BaseModel):
    battle_id: int
    mode: str
    status: str
    is_ranked: bool
    round_count: int
    round_seconds: int
    current_round_index: int
    you: BattleOpponentView
    opponent: BattleOpponentView
    current_round: BattleRoundView | None = None
    rounds: list[BattleRoundView] = []
    waiting_for_opponent: bool = False
    is_ai_battle: bool = False


class BattleFinishResponse(BaseModel):
    battle_id: int
    won: bool | None
    is_draw: bool = False
    your_score: int
    opponent_score: int
    xp_earned: int
    rating_before: int
    rating_after: int
    rating_delta: int
    win_streak: int
    headline: str
    subline: str


class BattleAnswerResponse(BaseModel):
    round: BattleRoundResultView
    state: BattleStateResponse | None = None
    finish: BattleFinishResponse | None = None


class ActiveBattleResponse(BaseModel):
    active: bool
    state: BattleStateResponse | None = None


class BattleProfileResponse(BaseModel):
    rating: int
    xp: int
    wins: int
    losses: int
    win_rate: float
    win_streak: int
    best_win_streak: int
    league: str
    battles_played: int
    weekly_xp: int
    global_rank: int | None = None


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: int
    username: str
    rating: int
    xp: int
    wins: int
    win_streak: int
    league: str
    is_you: bool = False


class LeaderboardResponse(BaseModel):
    scope: str
    season_week: str | None = None
    your_rank: int | None = None
    entries: list[LeaderboardEntry]


