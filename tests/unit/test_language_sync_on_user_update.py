"""Unit tests: language sync orchestration in UserCommandService.update_user."""

from unittest.mock import AsyncMock

import pytest

from app.models.user import User
from app.schemas.user import UserUpdate
from app.services.users.user_service import UserCommandService


def _make_user(*, user_id: int = 42, preferred_language: str = "uk") -> User:
    return User(
        id=user_id,
        public_id=100_001,
        email="test@example.com",
        username="testuser",
        hashed_password="hashed",
        preferred_language=preferred_language,
    )


@pytest.mark.asyncio
async def test_update_user_triggers_sync_and_invalidation_on_language_change() -> None:
    db = AsyncMock()
    service = UserCommandService(db)
    user = _make_user(preferred_language="uk")

    service.user_access = AsyncMock()
    service.user_access.get_user_or_404 = AsyncMock(return_value=user)
    service.language_sync = AsyncMock()
    service.language_sync.sync_word_translations_for_user = AsyncMock(return_value=2)
    service.language_invalidation = AsyncMock()
    service.language_invalidation.invalidate_for_user = AsyncMock(return_value=1)

    await service.update_user(42, UserUpdate(preferred_language="da"))

    service.language_sync.sync_word_translations_for_user.assert_awaited_once_with(
        42,
        "da",
    )
    service.language_invalidation.invalidate_for_user.assert_awaited_once_with(42)
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(user)
    assert user.preferred_language == "da"


@pytest.mark.asyncio
async def test_update_user_skips_sync_when_language_unchanged() -> None:
    db = AsyncMock()
    service = UserCommandService(db)
    user = _make_user(preferred_language="uk")

    service.user_access = AsyncMock()
    service.user_access.get_user_or_404 = AsyncMock(return_value=user)
    service.language_sync = AsyncMock()
    service.language_sync.sync_word_translations_for_user = AsyncMock()
    service.language_invalidation = AsyncMock()
    service.language_invalidation.invalidate_for_user = AsyncMock()

    await service.update_user(42, UserUpdate(preferred_language="uk"))

    service.language_sync.sync_word_translations_for_user.assert_not_awaited()
    service.language_invalidation.invalidate_for_user.assert_not_awaited()
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_user_skips_sync_when_only_username_changes() -> None:
    db = AsyncMock()
    service = UserCommandService(db)
    user = _make_user(preferred_language="uk")

    service.user_access = AsyncMock()
    service.user_access.get_user_or_404 = AsyncMock(return_value=user)
    service.user_validation = AsyncMock()
    service.user_validation.ensure_username_is_unique = AsyncMock()
    service.language_sync = AsyncMock()
    service.language_sync.sync_word_translations_for_user = AsyncMock()
    service.language_invalidation = AsyncMock()
    service.language_invalidation.invalidate_for_user = AsyncMock()

    await service.update_user(42, UserUpdate(username="newname"))

    service.language_sync.sync_word_translations_for_user.assert_not_awaited()
    service.language_invalidation.invalidate_for_user.assert_not_awaited()
    service.user_validation.ensure_username_is_unique.assert_awaited_once_with(
        "newname",
        exclude_user_id=42,
    )
    assert user.username == "newname"
