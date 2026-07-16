from datetime import datetime
from typing import Union

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.language_codes import default_language_code, resolve_canonical_language_code
from app.core.public_user_id import PUBLIC_ID_MAX, PUBLIC_ID_MIN
from app.helpers.english_level import parse_english_level
from app.models.word import DifficultyLevel


def _parse_preferred_language(value: object, *, allow_default: bool) -> str | None:
    if value is None:
        return None
    resolved = resolve_canonical_language_code(str(value))
    if resolved is not None:
        return resolved
    if allow_default:
        return default_language_code()
    raise ValueError(f"Unsupported preferred_language: {value}")


class UserBase(BaseModel):
    email: EmailStr
    username: str


class UserCreate(UserBase):
    password: str
    preferred_language: str | None = None
    english_level: Union[DifficultyLevel, str] | None = None

    @field_validator("english_level", mode="before")
    @classmethod
    def validate_english_level(cls, v):
        return parse_english_level(v)

    @field_validator("preferred_language", mode="before")
    @classmethod
    def validate_preferred_language(cls, v):
        return _parse_preferred_language(v, allow_default=False)


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    username: str | None = None
    is_active: bool | None = None
    preferred_language: str | None = None
    english_level: Union[DifficultyLevel, str] | None = None

    @field_validator("english_level", mode="before")
    @classmethod
    def validate_english_level(cls, v):
        parsed = parse_english_level(v)
        if v is not None and parsed is None:
            raise ValueError(
                "english_level must be CEFR (A1–C2) or beginner/medium/advanced"
            )
        return parsed

    @field_validator("preferred_language", mode="before")
    @classmethod
    def validate_preferred_language(cls, v):
        return _parse_preferred_language(v, allow_default=False)


class UserResponse(BaseModel):
    """API response: email as str so guest anon_*@guest.local addresses do not break EmailStr."""
    id: int
    public_id: int = Field(..., ge=PUBLIC_ID_MIN, le=PUBLIC_ID_MAX)
    email: str
    username: str
    is_active: bool
    tier: str
    preferred_language: str | None = None
    english_level: str
    created_at: datetime

    @field_validator("english_level", mode="before")
    @classmethod
    def validate_english_level_response(cls, v):
        if isinstance(v, DifficultyLevel):
            return v.value
        if isinstance(v, str):
            return v
        return str(v) if v else DifficultyLevel.B1.value

    @field_validator("preferred_language", mode="before")
    @classmethod
    def validate_preferred_language_response(cls, v):
        if v is None:
            return None
        return resolve_canonical_language_code(str(v)) or str(v)

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600
    refresh_token: str | None = None

    class Config:
        from_attributes = True


class RefreshTokenRequest(BaseModel):
    """Body for POST /auth/refresh (JSON)."""
    refresh_token: str


class UserDeleteRequest(BaseModel):
    password: str
    confirm: bool = True


class AnonymousLoginRequest(BaseModel):
    installation_id: str


class LogoutRequest(BaseModel):
    refresh_token: str


class PublicUserProfileResponse(BaseModel):
    """Public user preview by public_id (friend lookup before sending a request)."""

    public_id: int = Field(..., ge=PUBLIC_ID_MIN, le=PUBLIC_ID_MAX)
    username: str
    rating: int = 1000
    win_streak: int = 0
    league: str = "bronze"
