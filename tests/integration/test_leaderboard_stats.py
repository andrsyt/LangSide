"""Integration: battle leaderboard and home stats."""

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_battle_leaderboard_global(client, auth_headers) -> None:
    response = await client.get(
        "/api/v1/battles/leaderboard?scope=global",
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["scope"] == "global"
    assert isinstance(body["entries"], list)


@pytest.mark.asyncio
async def test_battle_leaderboard_weekly(client, auth_headers) -> None:
    response = await client.get(
        "/api/v1/battles/leaderboard?scope=weekly",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["season_week"] is not None


@pytest.mark.asyncio
async def test_home_stats(client, auth_headers) -> None:
    response = await client.get("/api/v1/stats/home", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total_words"] >= 0
    assert body["learning_words"] >= 0
