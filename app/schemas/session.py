"""
Pydantic schemas for sessions.

Keep schemas simple so the Swift client can decode them easily.
"""

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel

from app.schemas.word import WordResponse


Grade = Literal["EASY", "HARD"]


class SessionStartResponse(BaseModel):
    """Response for starting or fetching today's session."""

    session_id: int
    session_date: date
    goal: int
    words: list[WordResponse]
    recommended_goal: int
    streak_threshold: int
    can_extend: bool = True
    done: int = 0
    total: int = 0
    soft_goal_met: bool = False
    sources_breakdown: dict[str, int] = {}
    words_ready: bool = False
    skipped_count: int = 0
    message: str | None = None


class SessionExtendResponse(BaseModel):
    """Response after extending an active session with more cards."""

    session_id: int
    added: int
    total: int
    done: int
    goal: int
    words: list[WordResponse]
    recommended_goal: int
    streak_threshold: int
    can_extend: bool = True
    soft_goal_met: bool = False


class SessionCardResponse(BaseModel):
    """Next card in the session."""

    session_id: int
    item_id: int
    position: int
    total: int
    word: WordResponse


class SubmitAnswerRequest(BaseModel):
    """
    Client sends:
    - word_id: which word is being answered
    - is_correct: result (trusted from client for now; may validate via user_translation later)
    - grade: EASY/HARD (optional)
    """

    word_id: int
    is_correct: bool
    grade: Optional[Grade] = None


class SubmitAnswerResponse(BaseModel):
    """Payload returned after an answer is submitted."""

    word: WordResponse
    is_correct: bool
    next_review_at: Optional[str] = None  # string for easier Swift decoding (can become datetime later)
    done: int
    total: int
    recommended_goal: int
    streak_threshold: int
    soft_goal_met: bool = False


class SessionSummaryResponse(BaseModel):
    """Summary after the session is finished."""

    session_id: int
    total: int
    correct: int
    incorrect: int
    finished: bool
    streak_threshold: int
    soft_goal_met: bool = False

