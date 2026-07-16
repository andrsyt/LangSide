"""
Checks for NULL and duplicate token_hash before the align-nullability migration.
Uses DATABASE_URL from the environment or project-root .env (same as Alembic).

  python -m app.scripts.check_pre_migration_nulls
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text


def sync_database_url(raw: str) -> str:
    return raw.replace("+asyncpg", "").replace("postgresql+asyncpg://", "postgresql://")


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    load_dotenv(root / ".env", override=False)

    raw = os.environ.get("DATABASE_URL", "")
    if not raw:
        print("DATABASE_URL is not set (neither in the environment nor in .env).", file=sys.stderr)
        return 1

    url = sync_database_url(raw)
    engine = create_engine(url)

    checks: list[tuple[str, str]] = [
        ("anti_confusion_session.created_at", "SELECT COUNT(*) FROM anti_confusion_session WHERE created_at IS NULL"),
        ("common_words.created_at", "SELECT COUNT(*) FROM common_words WHERE created_at IS NULL"),
        ("double_recall_sessions.created_at", "SELECT COUNT(*) FROM double_recall_sessions WHERE created_at IS NULL"),
        ("quests.is_completed", "SELECT COUNT(*) FROM quests WHERE is_completed IS NULL"),
        ("quests.created_at", "SELECT COUNT(*) FROM quests WHERE created_at IS NULL"),
        ("quests.is_retry", "SELECT COUNT(*) FROM quests WHERE is_retry IS NULL"),
        ("sessions.created_at", "SELECT COUNT(*) FROM sessions WHERE created_at IS NULL"),
        ("test_sessions.created_at", "SELECT COUNT(*) FROM test_sessions WHERE created_at IS NULL"),
        ("usage.created_at", 'SELECT COUNT(*) FROM "usage" WHERE created_at IS NULL'),
        ("users.is_active", "SELECT COUNT(*) FROM users WHERE is_active IS NULL"),
        ("users.tier", "SELECT COUNT(*) FROM users WHERE tier IS NULL"),
        ("users.created_at", "SELECT COUNT(*) FROM users WHERE created_at IS NULL"),
        ("word_cards.created_at", "SELECT COUNT(*) FROM word_cards WHERE created_at IS NULL"),
        ("words.created_at", "SELECT COUNT(*) FROM words WHERE created_at IS NULL"),
        ("words.is_selected_for_test", "SELECT COUNT(*) FROM words WHERE is_selected_for_test IS NULL"),
    ]

    dup_sql = """
        SELECT COUNT(*) FROM (
            SELECT token_hash FROM refresh_tokens GROUP BY token_hash HAVING COUNT(*) > 1
        ) AS d
    """

    bad = False
    with engine.connect() as conn:
        for label, sql in checks:
            n = conn.execute(text(sql)).scalar_one()
            print(f"{label}: null_rows={n}")
            if n:
                bad = True

        dup_groups = conn.execute(text(dup_sql)).scalar_one()
        print(f"refresh_tokens duplicate token_hash groups: {dup_groups}")
        if dup_groups:
            bad = True

    if bad:
        print("\nFAILED: fix data before: alembic upgrade head", file=sys.stderr)
        return 1

    print("\nOK: run alembic upgrade head")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
