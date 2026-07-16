"""Integration: user profile english_level."""

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_update_english_level_medium(client, auth_headers) -> None:
    response = await client.put(
        "/api/v1/users/me",
        headers=auth_headers,
        json={"english_level": "medium"},
    )
    assert response.status_code == 200
    assert response.json()["english_level"] == "B1"

    me = await client.get("/api/v1/users/me", headers=auth_headers)
    assert me.json()["english_level"] == "B1"


@pytest.mark.asyncio
async def test_update_english_level_b2(client, auth_headers) -> None:
    response = await client.put(
        "/api/v1/users/me",
        headers=auth_headers,
        json={"english_level": "B2"},
    )
    assert response.status_code == 200
    assert response.json()["english_level"] == "B2"
