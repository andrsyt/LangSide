from __future__ import annotations

from app.models.word import DifficultyLevel

UI_LEVEL_TO_CEFR = {
    "beginner": DifficultyLevel.A2,
    "medium": DifficultyLevel.B1,
    "advanced": DifficultyLevel.B2,
}

CEFR_TO_UI = {level: key for key, level in UI_LEVEL_TO_CEFR.items()}

CEFR_ORDER = [
    DifficultyLevel.A1, DifficultyLevel.A2, DifficultyLevel.B1,
    DifficultyLevel.B2, DifficultyLevel.C1, DifficultyLevel.C2,
]

def levels_for_user(center: DifficultyLevel) -> list[DifficultyLevel]:
    i = CEFR_ORDER.index(center)
    lo = max(0, i - 1)
    hi = min(len(CEFR_ORDER) - 1, i + 1)
    return CEFR_ORDER[lo:hi+1]


def parse_english_level(value: str | DifficultyLevel | None) -> DifficultyLevel | None:
    """Parse CEFR code (B1) or UI key (medium) into DifficultyLevel."""
    if value is None:
        return None
    if isinstance(value, DifficultyLevel):
        return value
    if not isinstance(value, str):
        return None

    normalized = value.strip().lower()
    if not normalized:
        return None

    ui_level = UI_LEVEL_TO_CEFR.get(normalized)
    if ui_level is not None:
        return ui_level

    try:
        return DifficultyLevel(normalized.upper())
    except ValueError:
        for level in DifficultyLevel:
            if level.value.lower() == normalized:
                return level
    return None
