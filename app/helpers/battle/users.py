from __future__ import annotations

import re

from app.models.user import User

_TEST_USERNAME = re.compile(r"^(btest|test_|anon_)", re.IGNORECASE)


def is_eligible_battle_user(user: User) -> bool:
    """Real accounts only — skip guests, dev registrations, and anon users."""
    if user.is_anonymous:
        return False
    username = (user.username or "").strip()
    email = (user.email or "").strip().lower()
    if not username:
        return False
    if _TEST_USERNAME.match(username):
        return False
    if email.endswith("@guest.local"):
        return False
    if email.startswith("btest") or "@test." in email:
        return False
    return True


def public_display_name(user: User | None, *, fallback: str = "Player") -> str:
    if user is None or not is_eligible_battle_user(user):
        return fallback
    return (user.username or fallback)[:64]
