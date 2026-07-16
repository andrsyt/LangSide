"""Unit tests: GET /languages and legacy /languages/translation alias."""

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from app.api.v1.endpoints.languages import router
from app.core.language_codes import SUPPORTED_TRANSLATION_LANGUAGES, default_language_code


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(router, prefix="/languages")
    return TestClient(app)


def test_list_languages_root(client: TestClient) -> None:
    response = client.get("/languages")

    assert response.status_code == 200
    data = response.json()
    assert len(data["languages"]) == len(SUPPORTED_TRANSLATION_LANGUAGES)
    assert data["default_code"] == default_language_code()


def test_list_languages_translation_alias_matches_root(client: TestClient) -> None:
    root = client.get("/languages").json()
    translation = client.get("/languages/translation").json()

    assert translation == root


def test_language_option_has_required_fields(client: TestClient) -> None:
    data = client.get("/languages").json()
    first = data["languages"][0]

    assert set(first) == {"code", "name_en", "source"}
    assert first["source"] in {"dictionary", "api"}
