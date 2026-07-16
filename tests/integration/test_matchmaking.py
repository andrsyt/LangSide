"""Integration: matchmaking queue and AI fallback."""

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_matchmaking_join_ai_starts_battle(client, auth_headers) -> None:
    with patch(
        "app.services.battle.battle_service.BattleRoundPoolBuilder.pick_round_count",
        return_value=2,
    ):
        response = await client.post(
            "/api/v1/battles/matchmaking/join",
            headers=auth_headers,
            json={"mode": "ai"},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"ai_ready", "matched"}
    assert body["battle"] is not None
    assert body["battle"]["is_ai_battle"] is True


@pytest.mark.asyncio
async def test_matchmaking_searching_and_cancel(client, auth_headers) -> None:
    join = await client.post(
        "/api/v1/battles/matchmaking/join",
        headers=auth_headers,
        json={"mode": "quick"},
    )
    assert join.status_code == 200
    body = join.json()
    assert body["status"] == "searching"
    ticket_id = body["ticket_id"]
    assert body["search_message"]

    status = await client.get(
        f"/api/v1/battles/matchmaking/{ticket_id}",
        headers=auth_headers,
    )
    assert status.status_code == 200
    assert status.json()["status"] == "searching"

    cancel = await client.delete(
        f"/api/v1/battles/matchmaking/{ticket_id}",
        headers=auth_headers,
    )
    assert cancel.status_code == 200

    after = await client.get(
        f"/api/v1/battles/matchmaking/{ticket_id}",
        headers=auth_headers,
    )
    assert after.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_matchmaking_pvp_two_registered_players(
    client,
    registered_auth_headers,
    second_registered_auth_headers,
) -> None:
    with patch(
        "app.services.battle.battle_service.BattleRoundPoolBuilder.pick_round_count",
        return_value=2,
    ):
        first = await client.post(
            "/api/v1/battles/matchmaking/join",
            headers=registered_auth_headers,
            json={"mode": "quick"},
        )
        second = await client.post(
            "/api/v1/battles/matchmaking/join",
            headers=second_registered_auth_headers,
            json={"mode": "quick"},
        )
    assert first.status_code == 200
    assert second.status_code == 200
    statuses = {first.json()["status"], second.json()["status"]}
    assert "matched" in statuses
    matched = first if first.json()["status"] == "matched" else second
    assert matched.json()["battle"] is not None
    assert matched.json()["opponent"] is not None
    assert matched.json()["opponent"]["is_bot"] is False
