from __future__ import annotations

import csv
import logging
from csv import DictReader
from pathlib import Path

from httpx import AsyncClient

from app.core.config import settings
from app.core.language_codes import (
    CSV_LANGUAGE_SOURCES,
    default_language_code,
    is_dictionary_backed,
    language_code_for_google,
    resolve_canonical_language_code,
)
from app.helpers.text_utils import normalize_translation

logger = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parents[2]

_dictionaries: dict[str, dict[str, str]] = {}


class TranslationDictionaryHelper:
    """Handles local CSV-backed translation dictionaries."""

    @staticmethod
    def get_csv_entry(canonical_language: str) -> tuple[Path, str] | None:
        entry = CSV_LANGUAGE_SOURCES.get(canonical_language)
        if entry is None:
            return None
        csv_rel_path, language_name = entry
        return BASE_DIR / csv_rel_path, language_name

    @classmethod
    def load_translation_for_language(cls, canonical_language: str) -> dict[str, str]:
        if canonical_language in _dictionaries:
            return _dictionaries[canonical_language]

        csv_entry = cls.get_csv_entry(canonical_language)
        if csv_entry is None:
            _dictionaries[canonical_language] = {}
            return _dictionaries[canonical_language]

        csv_path, language_name = csv_entry
        if not csv_path.exists():
            _dictionaries[canonical_language] = {}
            return _dictionaries[canonical_language]

        with open(csv_path, "r", encoding="utf-8") as file:
            reader = DictReader(file)
            translations = {
                row["English"].lower().strip(): row[language_name] for row in reader
            }

        _dictionaries[canonical_language] = translations
        return translations

    @classmethod
    def get_translation_from_local_dict(
        cls,
        word: str,
        canonical_language: str,
    ) -> str | None:
        normalized_word = word.lower().strip()
        translations = cls.load_translation_for_language(canonical_language)
        return translations.get(normalized_word)

    @classmethod
    def save_translation_to_local_dict_and_csv(
        cls,
        word: str,
        canonical_language: str,
        translated: str,
    ) -> None:
        normalized_word = word.lower().strip()
        translations = cls.load_translation_for_language(canonical_language)
        translations[normalized_word] = translated

        entry = CSV_LANGUAGE_SOURCES.get(canonical_language)
        if not entry:
            return

        csv_rel_path, column_name = entry
        csv_path = BASE_DIR / csv_rel_path
        with open(csv_path, "a", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=["English", column_name])
            writer.writerow({"English": word.strip(), column_name: translated})


class TranslationApiHelper:
    """Calls external translation providers."""

    @staticmethod
    async def translate_via_google(word: str, canonical_language: str) -> str | None:
        if not settings.GOOGLE_TRANSLATION_KEY:
            logger.warning("GOOGLE_TRANSLATION_KEY not set; skipping Google Translate")
            return None

        try:
            google_target = language_code_for_google(canonical_language)
        except ValueError:
            logger.error("Unknown language: %s", canonical_language)
            return None

        params = {
            "key": settings.GOOGLE_TRANSLATION_KEY,
            "q": word,
            "source": "en",
            "target": google_target,
        }
        try:
            async with AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    settings.GOOGLE_TRANSLATE_URL, params=params
                )
                response.raise_for_status()
                data = response.json()
                return data["data"]["translations"][0]["translatedText"]
        except Exception as exc:
            logger.error("Translation error for '%s': %s", word, exc)
            return None


async def translate_word(word: str, target_language: str) -> str | None:
    original_word = word.strip()
    if not original_word:
        return None

    canonical = (
        resolve_canonical_language_code(target_language) or default_language_code()
    )
    normalized_word = original_word.lower()

    if is_dictionary_backed(canonical):
        local_translation = TranslationDictionaryHelper.get_translation_from_local_dict(
            normalized_word,
            canonical,
        )
        if local_translation:
            return local_translation

    translated = await TranslationApiHelper.translate_via_google(
        original_word, canonical
    )
    if translated and translated.strip():
        return translated.strip()
    return None


async def translate_and_normalize(word: str, target_language: str) -> str | None:
    raw = await translate_word(word, target_language)
    if not raw:
        return None
    return normalize_translation(raw) or None
