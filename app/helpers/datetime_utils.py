from __future__ import annotations

from datetime import datetime, timezone


def utc_naive_now() -> datetime:
    """UTC as naive datetime for Postgres TIMESTAMP WITHOUT TIME ZONE."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def elapsed_seconds_since(created_at: datetime | None, *, cap: float = 120.0) -> float:
    if created_at is None:
        return 0.0
    now = utc_naive_now()
    if created_at.tzinfo is not None:
        created = created_at.astimezone(timezone.utc).replace(tzinfo=None)
    else:
        created = created_at
    return max(0.0, min((now - created).total_seconds(), cap))
