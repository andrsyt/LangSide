"""Integration: health and anonymous auth."""

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_health(client) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_anonymous_login_returns_token(client) -> None:
    response = await client.post(
        "/api/v1/auth/anonymous",
        json={"installation_id": "pytest-install-1"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["access_token"]
    assert data["token_type"] == "Bearer"


@pytest.mark.asyncio
async def test_users_me_requires_auth(client) -> None:
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_users_me_after_anonymous(auth_headers, client) -> None:
    response = await client.get("/api/v1/users/me", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["english_level"] == "B1"
    assert body["public_id"] >= 1_000_000
