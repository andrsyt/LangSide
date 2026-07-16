from __future__ import annotations

from typing import Final

SUPPORTED_TRANSLATION_LANGUAGES: Final[frozenset[str]] = frozenset(
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

LEGACY_LANGUAGE_ALIASES: Final[dict[str, str]] = {
    "ukrainian": "uk",
    "russian": "ru",
    "polish": "pl",
    "german": "de",
    "french": "fr",
    "spanish": "es",
    "italian": "it",
}

GOOGLE_TARGET_CODES: Final[dict[str, str]] = {
    "zh-Hans": "zh-CN",
    "zh-Hant": "zh-TW",
    "pt-BR": "pt",
    "pt-PT": "pt",
}

CSV_LANGUAGE_SOURCES: Final[dict[str, tuple[str, str]]] = {
    "uk": ("localization/eng-ukr.csv", "Ukrainian"),
    "ru": ("localization/eng-rus.csv", "Russian"),
    "pl": ("localization/eng-pol.csv", "Polish"),
    "de": ("localization/eng-ger.csv", "German"),
    "fr": ("localization/eng-fra.csv", "French"),
    "es": ("localization/eng-spa.csv", "Spanish"),
    "it": ("localization/eng-ita.csv", "Italian"),
}

TRANSLATION_LANGUAGE_NAMES: Final[dict[str, str]] = {
    "uk": "Ukrainian",
    "ru": "Russian",
    "pl": "Polish",
    "de": "German",
    "fr": "French",
    "es": "Spanish",
    "it": "Italian",
    "ro": "Romanian",
    "tr": "Turkish",
    "ar": "Arabic",
    "hi": "Hindi",
    "zh-Hans": "Chinese (Simplified)",
    "zh-Hant": "Chinese (Traditional)",
    "ja": "Japanese",
    "ko": "Korean",
    "pt-BR": "Portuguese (Brazil)",
    "pt-PT": "Portuguese (Portugal)",
    "nl": "Dutch",
    "cs": "Czech",
    "hu": "Hungarian",
    "sv": "Swedish",
    "da": "Danish",
    "fi": "Finnish",
    "vi": "Vietnamese",
    "id": "Indonesian",
}

_SUPPORTED_LOWER_MAP: Final[dict[str, str]] = {
    code.lower(): code for code in SUPPORTED_TRANSLATION_LANGUAGES
}


def normalize_language_code(language_code: str | None) -> str | None:
    """Normalize raw client input to a canonical or legacy-resolved code."""
    if language_code is None or not language_code.strip():
        return None

    cleaned = language_code.strip()
    legacy_key = cleaned.lower()
    if legacy_key in LEGACY_LANGUAGE_ALIASES:
        return LEGACY_LANGUAGE_ALIASES[legacy_key]

    return _SUPPORTED_LOWER_MAP.get(legacy_key)


def resolve_canonical_language_code(language_code: str | None) -> str | None:
    """Return a supported canonical code or None for unknown values."""
    normalized_code = normalize_language_code(language_code)
    if normalized_code is None:
        return None
    if normalized_code in SUPPORTED_TRANSLATION_LANGUAGES:
        return normalized_code
    return None


def language_code_for_google(canonical_code: str) -> str:
    """Map canonical translation language to a Google Translate target code."""
    if canonical_code not in SUPPORTED_TRANSLATION_LANGUAGES:
        raise ValueError(f"Unsupported language code: {canonical_code}")
    return GOOGLE_TARGET_CODES.get(canonical_code, canonical_code)


def default_language_code() -> str:
    """Default translation language when user preference is unset."""
    return "uk"


def is_dictionary_backed(canonical_code: str) -> bool:
    """Return True when a local Oxford CSV backs the language."""
    return canonical_code in CSV_LANGUAGE_SOURCES
