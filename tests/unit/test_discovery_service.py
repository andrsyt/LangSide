"""Unit tests: DiscoveryWordService with mocked repositories."""

from datetime import date
from unittest.mock import AsyncMock

import pytest

from app.models.word import DifficultyLevel, StudyStatus, Word
from app.services.sessions.discovery_word_service import DiscoveryWordService


@pytest.mark.asyncio
async def test_discovery_slots_remaining_respects_daily_max() -> None:
    db = AsyncMock()
    service = DiscoveryWordService(db, user_id=7)
    service.session_items = AsyncMock()
    service.session_items.count_discovery_for_user_on_date = AsyncMock(return_value=4)

    remaining = await service.discovery_slots_remaining(date.today())
    assert remaining == 0


@pytest.mark.asyncio
async def test_ensure_word_skips_mastered() -> None:
    db = AsyncMock()
    service = DiscoveryWordService(db, user_id=7)
    service.words = AsyncMock()
    mastered = Word(
        id=1,
        user_id=7,
        word_text="price",
        study_status=StudyStatus.MASTERED.value,
    )
    service.words.get_by_text_for_user = AsyncMock(return_value=mastered)

    result = await service.ensure_word_for_user("price", DifficultyLevel.B1)
    assert result is None


@pytest.mark.asyncio
async def test_pick_discovery_returns_empty_when_limit_reached() -> None:
    db = AsyncMock()
    service = DiscoveryWordService(db, user_id=7)
    service.session_items = AsyncMock()
    service.session_items.count_discovery_for_user_on_date = AsyncMock(return_value=4)

    result = await service.pick_discovery_words(
        DifficultyLevel.B1,
        count=3,
        session_date=date.today(),
    )
    assert result == []


@pytest.mark.asyncio
async def test_pick_discovery_from_catalog() -> None:
    db = AsyncMock()
    service = DiscoveryWordService(db, user_id=7)
    service.session_items = AsyncMock()
    service.session_items.count_discovery_for_user_on_date = AsyncMock(return_value=0)
    service.common_words = AsyncMock()
    service.common_words.fetch_random_by_levels = AsyncMock(
        return_value=[("price", DifficultyLevel.B1), ("water", DifficultyLevel.A1)],
    )

    word_price = Word(
        id=10,
        user_id=7,
        word_text="price",
        translation="ціна",
        explanation="The amount of money for which something is sold.",
        study_status=StudyStatus.LEARNING.value,
    )
    word_water = Word(
        id=11,
        user_id=7,
        word_text="water",
        translation="вода",
        explanation="A clear liquid that has no colour or taste.",
        study_status=StudyStatus.LEARNING.value,
    )

    async def ensure_side_effect(text: str, level: DifficultyLevel, **kwargs):
        if text == "price":
            return word_price
        if text == "water":
            return word_water
        return None

    service.ensure_word_for_user = AsyncMock(side_effect=ensure_side_effect)

    picked = await service.pick_discovery_words(
        DifficultyLevel.B1,
        count=2,
        session_date=date.today(),
    )
    assert len(picked) == 2
    assert {word.word_text for word in picked} == {"price", "water"}
