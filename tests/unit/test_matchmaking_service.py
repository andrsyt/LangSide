"""Unit tests: MatchmakingService (no database)."""

import pytest
from fastapi import HTTPException
from unittest.mock import AsyncMock

from app.schemas.battle import BattleModeRequest, MatchmakingJoinRequest
from app.services.battle.matchmaking_service import MatchmakingService


@pytest.mark.asyncio
async def test_join_voice_returns_not_implemented() -> None:
    service = MatchmakingService(AsyncMock(), user_id=1)
    with pytest.raises(HTTPException) as exc_info:
        await service.join(MatchmakingJoinRequest(mode=BattleModeRequest.voice))
    assert exc_info.value.status_code == 501
