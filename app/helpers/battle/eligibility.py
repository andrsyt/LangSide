from __future__ import annotations

from sqlalchemy import not_, or_
from sqlalchemy.sql.elements import ColumnElement

from app.models.user import User


def non_test_user_sql_conditions() -> list[ColumnElement[bool]]:
    """Shared leaderboard / matchmaking filters for real player accounts."""
    return [
        User.is_anonymous.is_(False),
        not_(User.username.ilike("btest%")),
        not_(User.username.ilike("test_%")),
        not_(User.username.ilike("anon_%")),
        not_(or_(User.email.ilike("%@guest.local"), User.email.ilike("btest%@"))),
    ]
