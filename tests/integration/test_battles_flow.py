"""Integration: battle profile, active guard, quick AI duel."""

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_battle_profile(client, auth_headers) -> None:
    response = await client.get("/api/v1/battles/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["rating"] == 1000
    assert data["league"] == "bronze"
    assert "win_rate" in data


@pytest.mark.asyncio
async def test_active_battle_empty(client, auth_headers) -> None:
    response = await client.get("/api/v1/battles/active", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["active"] is False


@pytest.mark.asyncio
async def test_quick_start_ai_battle_three_rounds(client, auth_headers) -> None:
    with patch(
        "app.services.battle.battle_service.BattleRoundPoolBuilder.pick_round_count",
        return_value=3,
    ):
        start = await client.post(
            "/api/v1/battles/quick-start",
            headers=auth_headers,
            json={"mode": "ai"},
        )
    assert start.status_code == 200
    state = start.json()
    battle_id = state["battle_id"]
    assert state["round_count"] == 3
    assert state["is_ai_battle"] is True

    active = await client.get("/api/v1/battles/active", headers=auth_headers)
    assert active.json()["active"] is True

    finish_payload = None
    for round_index in range(3):
        current = await client.get(
            f"/api/v1/battles/{battle_id}/state",
            headers=auth_headers,
        )
        assert current.status_code == 200
        current_round = current.json()["current_round"]
        assert current_round is not None
        choices = current_round["choices"]
        assert len(choices) >= 2

        answer = await client.post(
            f"/api/v1/battles/{battle_id}/rounds/{round_index}/answer",
            headers=auth_headers,
            json={"answer": choices[0], "time_ms": 2000},
        )
        assert answer.status_code == 200
        round_body = answer.json()["round"]
        if not round_body["player_correct"]:
            answer = await client.post(
                f"/api/v1/battles/{battle_id}/rounds/{round_index}/answer",
                headers=auth_headers,
                json={"answer": round_body["correct_answer"], "time_ms": 2000},
            )
            assert answer.status_code == 200
            round_body = answer.json()["round"]

        if answer.json().get("finish"):
            finish_payload = answer.json()["finish"]
            break

    assert finish_payload is not None
    assert "xp_earned" in finish_payload

    active_after = await client.get("/api/v1/battles/active", headers=auth_headers)
    assert active_after.json()["active"] is False


@pytest.mark.asyncio
async def test_cannot_start_second_active_battle(client, auth_headers) -> None:
    with patch(
        "app.services.battle.battle_service.BattleRoundPoolBuilder.pick_round_count",
        return_value=2,
    ):
        first = await client.post(
            "/api/v1/battles/quick-start",
            headers=auth_headers,
            json={"mode": "ai"},
        )
    assert first.status_code == 200

    second = await client.post(
        "/api/v1/battles/quick-start",
        headers=auth_headers,
        json={"mode": "ai"},
    )
    assert second.status_code == 409
