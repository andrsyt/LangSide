"""Integration: words CRUD."""

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_create_and_list_words(client, auth_headers) -> None:
    create = await client.post(
        "/api/v1/words/",
        headers=auth_headers,
        json={"word_text": "notebook"},
    )
    assert create.status_code == 200
    created = create.json()
    assert created["word_text"] == "notebook"
    word_id = created["id"]

    listing = await client.get("/api/v1/words/", headers=auth_headers)
    assert listing.status_code == 200
    ids = {row["id"] for row in listing.json()}
    assert word_id in ids

    one = await client.get(f"/api/v1/words/{word_id}", headers=auth_headers)
    assert one.status_code == 200
    assert one.json()["word_text"] == "notebook"


@pytest.mark.asyncio
async def test_update_difficulty_and_delete(client, auth_headers) -> None:
    create = await client.post(
        "/api/v1/words/",
        headers=auth_headers,
        json={"word_text": "vocabulary"},
    )
    word_id = create.json()["id"]

    patch = await client.patch(
        f"/api/v1/words/{word_id}/difficulty",
        headers=auth_headers,
        json={"difficulty": "B2"},
    )
    assert patch.status_code == 200
    assert patch.json()["difficulty"] == "B2"

    delete = await client.delete(
        f"/api/v1/words/{word_id}",
        headers=auth_headers,
    )
    assert delete.status_code == 204

    missing = await client.get(f"/api/v1/words/{word_id}", headers=auth_headers)
    assert missing.status_code == 404


@pytest.mark.asyncio
async def test_words_review_endpoint(client, auth_headers, learning_words) -> None:
    response = await client.get(
        "/api/v1/words/review?limit=5",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)
