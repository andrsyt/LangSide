"""Unit tests: canonical translation language codes (Stage 1)."""

import pytest

from app.core.language_codes import (
    CSV_LANGUAGE_SOURCES,
    GOOGLE_TARGET_CODES,
    LEGACY_LANGUAGE_ALIASES,
    SUPPORTED_TRANSLATION_LANGUAGES,
    default_language_code,
    is_dictionary_backed,
    language_code_for_google,
    resolve_canonical_language_code,
)

EXPECTED_SUPPORTED = frozenset(
    {
        "uk",
        "ru",
        "pl",
        "de",
        "fr",
        "es",
        "it",
        "ro",
        "tr",
        "ar",
        "hi",
        "zh-Hans",
        "zh-Hant",
        "ja",
        "ko",
        "pt-BR",
        "pt-PT",
        "nl",
        "cs",
        "hu",
        "sv",
        "da",
        "fi",
        "vi",
        "id",
    }
)


def test_supported_languages_count_and_set() -> None:
    assert len(SUPPORTED_TRANSLATION_LANGUAGES) == 25
    assert SUPPORTED_TRANSLATION_LANGUAGES == EXPECTED_SUPPORTED


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("ukrainian", "uk"),
        ("Ukrainian", "uk"),
        ("UK", "uk"),
        ("uk", "uk"),
        ("  pl  ", "pl"),
        ("ro", "ro"),
        ("zh-Hans", "zh-Hans"),
        ("zh-hans", "zh-Hans"),
        ("pt-BR", "pt-BR"),
        ("pt-br", "pt-BR"),
    ],
)
def test_resolve_canonical_language_code(raw: str, expected: str) -> None:
    assert resolve_canonical_language_code(raw) == expected


@pytest.mark.parametrize(
    "raw",
    ["zz", "klingon", "", "   "],
)
def test_resolve_unknown_or_empty_returns_none(raw: str) -> None:
    assert resolve_canonical_language_code(raw) is None


def test_resolve_none_returns_none() -> None:
    assert resolve_canonical_language_code(None) is None  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("canonical", "google_code"),
    [
        ("zh-Hans", "zh-CN"),
        ("zh-Hant", "zh-TW"),
        ("pt-BR", "pt"),
        ("pt-PT", "pt"),
        ("ro", "ro"),
        ("de", "de"),
    ],
)
def test_language_code_for_google(canonical: str, google_code: str) -> None:
    assert language_code_for_google(canonical) == google_code


def test_language_code_for_google_unknown_raises() -> None:
    with pytest.raises(ValueError, match="Unsupported language code"):
        language_code_for_google("zz")


def test_default_language_code() -> None:
    assert default_language_code() == "uk"


def test_is_dictionary_backed() -> None:
    assert is_dictionary_backed("de") is True
    assert is_dictionary_backed("ro") is False


def test_legacy_aliases_map_to_supported_codes() -> None:
    for legacy, canonical in LEGACY_LANGUAGE_ALIASES.items():
        assert resolve_canonical_language_code(legacy) == canonical
        assert canonical in SUPPORTED_TRANSLATION_LANGUAGES


def test_csv_sources_keys_are_supported_dictionary_langs() -> None:
    assert set(CSV_LANGUAGE_SOURCES) == {"uk", "ru", "pl", "de", "fr", "es", "it"}
    for code in CSV_LANGUAGE_SOURCES:
        assert code in SUPPORTED_TRANSLATION_LANGUAGES


def test_google_target_codes_keys_are_supported() -> None:
    for code in GOOGLE_TARGET_CODES:
        assert code in SUPPORTED_TRANSLATION_LANGUAGES
