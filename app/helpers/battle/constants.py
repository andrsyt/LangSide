from __future__ import annotations

from app.models.battle import BattleLeague
from app.models.word import DifficultyLevel

AI_OPPONENT_NAME = "AI Coach"
ROUNDS_MIN = 10
ROUNDS_MAX = 15
ROUND_SECONDS = 15
CHOICES_PER_ROUND = 4
MATCHMAKING_AI_SECONDS = 7
MATCHMAKING_SEARCH_MAX_AGE_SECONDS = 120
BATTLE_STALE_HOURS = 2
BATTLE_TIMEOUT_ANSWER = "..."
BATTLE_TIMEOUT_TIME_MS = 15_000
MATCHMAKING_RANKED_RATING_WINDOW = 450
MATCHMAKING_CASUAL_RATING_WINDOW = 5000
BOT_ACCURACY_AI = 0.68
BOT_ACCURACY_OTHER = 0.72
DEFAULT_RATING = 1000
MIN_RATING = 400
ELO_K = 32

FALLBACK_WORDS: list[dict[str, str]] = [
    {"prompt": "ціна", "answer": "price"},
    {"prompt": "друг", "answer": "friend"},
    {"prompt": "час", "answer": "time"},
    {"prompt": "дім", "answer": "house"},
    {"prompt": "вода", "answer": "water"},
    {"prompt": "книга", "answer": "book"},
    {"prompt": "робота", "answer": "work"},
    {"prompt": "місто", "answer": "city"},
    {"prompt": "школа", "answer": "school"},
    {"prompt": "їжа", "answer": "food"},
    {"prompt": "день", "answer": "day"},
    {"prompt": "ніч", "answer": "night"},
    {"prompt": "рука", "answer": "hand"},
    {"prompt": "око", "answer": "eye"},
    {"prompt": "слово", "answer": "word"},
]

# Lower weight => rarer in random battle rounds (C1/C2 appear less often).
CEFR_BATTLE_WEIGHTS: dict[DifficultyLevel, float] = {
    DifficultyLevel.A1: 1.0,
    DifficultyLevel.A2: 0.95,
    DifficultyLevel.B1: 0.65,
    DifficultyLevel.B2: 0.45,
    DifficultyLevel.C1: 0.22,
    DifficultyLevel.C2: 0.12,
}

# Rows fetched from DB before weighted sampling (catalog is large).
CATALOG_FETCH_MULTIPLIER = 12

LEAGUE_THRESHOLDS: list[tuple[int, BattleLeague]] = [
    (1800, BattleLeague.DIAMOND),
    (1500, BattleLeague.PLATINUM),
    (1300, BattleLeague.GOLD),
    (1100, BattleLeague.SILVER),
    (0, BattleLeague.BRONZE),
]
