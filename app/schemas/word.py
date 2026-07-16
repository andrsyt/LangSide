from pydantic import BaseModel
from datetime import datetime

class WordBase(BaseModel):
    word_text: str

class WordCreate(WordBase):
    # user_id is not needed here — taken from the auth token
    pass

class WordUpdate(BaseModel):
    word_text: str | None = None
    translation: str | None = None
    explanation: str | None = None
    examples: str | None = None
    difficulty: str | None = None


class WordDifficultyUpdate(BaseModel):
    difficulty: str

class WordResponse(WordBase):
    id: int
    user_id: int 
    translation: str | None = None
    explanation: str | None = None
    examples: str | None = None
    difficulty: str | None = None
    created_at: datetime
    # Spaced-repetition fields
    study_status: str | None = None
    knowledge_level: int | None = None
    last_reviewed_at: datetime | None = None
    next_review_at: datetime | None = None
    review_count: int | None = None
    correct_count: int | None = None
    incorrect_count: int | None = None
    ease_factor: float | None = None
    session_source: str | None = None

    class Config:
        from_attributes = True


class WordCardBase(BaseModel):
    id: int
    word_id: int
    word_text: str
    translation: str
    explanation: str | None = None
    examples: list[str]
    synonyms: list[str]
    associations: list[str]
    created_at: datetime
