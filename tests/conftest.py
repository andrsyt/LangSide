"""Root pytest hooks (no DB — see tests/integration/conftest.py)."""

from __future__ import annotations

import os

# Unit collection imports app modules that instantiate Settings at import time.
# CI has no .env — provide safe defaults before any app import.
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/learn_english_db",
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("SECRET_KEY", "ci-test-secret-key-not-for-production")
os.environ.setdefault("ANON_SALT", "ci-test-anon-salt")

import pytest


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "integration: marks tests that need PostgreSQL (TEST_DATABASE_URL)",
    )
