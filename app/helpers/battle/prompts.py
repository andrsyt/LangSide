from __future__ import annotations

from app.core.language_codes import default_language_code, resolve_canonical_language_code
from app.helpers.translation_helper import TranslationDictionaryHelper


def battle_prompt_for_word(word_text: str, language: str) -> str:
    """Localized prompt (translation) for the English answer word."""
    canonical = resolve_canonical_language_code(language) or default_language_code()
    translation = TranslationDictionaryHelper.get_translation_from_local_dict(
        word_text,
        canonical,
    )
    if translation and translation.strip():
        return translation.strip()
    return word_text.strip()
