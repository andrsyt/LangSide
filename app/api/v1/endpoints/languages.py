"""Supported translation languages for word glosses and exercises."""

from fastapi import APIRouter

from app.core.language_codes import (
    SUPPORTED_TRANSLATION_LANGUAGES,
    TRANSLATION_LANGUAGE_NAMES,
    default_language_code,
    is_dictionary_backed,
)
from app.schemas.languages import (
    TranslationLanguageListResponse,
    TranslationLanguageOption,
)

router = APIRouter()


@router.get("", response_model=TranslationLanguageListResponse)
@router.get("/translation", response_model=TranslationLanguageListResponse)
async def list_translation_languages() -> TranslationLanguageListResponse:
    """Return supported translation languages for client pickers."""
    languages = [
        TranslationLanguageOption(
            code=code,
            name_en=TRANSLATION_LANGUAGE_NAMES[code],
            source="dictionary" if is_dictionary_backed(code) else "api",
        )
        for code in sorted(SUPPORTED_TRANSLATION_LANGUAGES, key=str.lower)
    ]
    return TranslationLanguageListResponse(
        languages=languages,
        default_code=default_language_code(),
    )
