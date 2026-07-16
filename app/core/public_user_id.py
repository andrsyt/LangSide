"""Public account ID (Standoff-style): UI and friend search only."""

PUBLIC_ID_MIN = 1_000_000
PUBLIC_ID_MAX = 99_999_999
PUBLIC_ID_INITIAL = PUBLIC_ID_MIN


def is_valid_public_id(value: int) -> bool:
    return PUBLIC_ID_MIN <= value <= PUBLIC_ID_MAX
