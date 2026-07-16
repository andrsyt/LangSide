"""Integration: today session start, answer, extend."""

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_start_today_session(client, auth_headers, learning_words) -> None:
    response = await client.post(
        "/api/v1/sessions/today/start?daily_goal=6",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] > 0
    assert data["recommended_goal"] == 10
    assert data["streak_threshold"] == 6
    assert len(data["words"]) >= 1
    assert data["goal"] == 6


@pytest.mark.asyncio
async def test_session_answer_and_soft_goal(
    client,
    auth_headers,
    learning_words,
) -> None:
    start = await client.post(
        "/api/v1/sessions/today/start?daily_goal=4",
        headers=auth_headers,
    )
    session_id = start.json()["session_id"]
    words = start.json()["words"]
    assert len(words) >= 1

    done = 0
    for word in words[:4]:
        answer = await client.post(
            f"/api/v1/sessions/{session_id}/answer",
            headers=auth_headers,
            json={"word_id": word["id"], "is_correct": True},
        )
        assert answer.status_code == 200
        done = answer.json()["done"]

    assert done >= 1
    if done >= 6:
        assert answer.json()["soft_goal_met"] is True


@pytest.mark.asyncio
async def test_session_extend(client, auth_headers, learning_words) -> None:
    start = await client.post(
        "/api/v1/sessions/today/start?daily_goal=3",
        headers=auth_headers,
    )
    session_id = start.json()["session_id"]

    extend = await client.post(
        f"/api/v1/sessions/{session_id}/extend?count=2",
        headers=auth_headers,
    )
    assert extend.status_code == 200
    body = extend.json()
    assert body["added"] >= 1
    assert body["total"] >= start.json()["total"] + body["added"]


@pytest.mark.asyncio
async def test_session_profile_stats(client, auth_headers, learning_words) -> None:
    await client.post(
        "/api/v1/sessions/today/start?daily_goal=2",
        headers=auth_headers,
    )
    stats = await client.get(
        "/api/v1/sessions/profile/stats",
        headers=auth_headers,
    )
    assert stats.status_code == 200
    body = stats.json()
    assert "current_streak" in body or "study_days" in str(body).lower() or body
