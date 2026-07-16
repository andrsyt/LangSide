from pydantic import BaseModel


class TranslationLanguageOption(BaseModel):
    code: str
    name_en: str
    source: str


class TranslationLanguageListResponse(BaseModel):
    languages: list[TranslationLanguageOption]
    default_code: str
