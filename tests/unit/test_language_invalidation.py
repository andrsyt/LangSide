"""Unit tests: UserLanguageSessionInvalidationService."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.helpers.user_language_invalidation import UserLanguageSessionInvalidationService


def _execute_result(rowcount: int) -> MagicMock:
    result = MagicMock()
    result.rowcount = rowcount
    return result


@pytest.mark.asyncio
async def test_invalidate_for_user_deletes_five_session_types() -> None:
    db = AsyncMock()
    db.execute = AsyncMock(return_value=_execute_result(1))

    service = UserLanguageSessionInvalidationService(db)
    deleted = await service.invalidate_for_user(42)

    assert deleted == 5
    assert db.execute.await_count == 5


@pytest.mark.asyncio
async def test_invalidate_for_user_returns_zero_when_nothing_deleted() -> None:
    db = AsyncMock()
    db.execute = AsyncMock(return_value=_execute_result(0))

    service = UserLanguageSessionInvalidationService(db)
    deleted = await service.invalidate_for_user(7)

    assert deleted == 0
    assert db.execute.await_count == 5
