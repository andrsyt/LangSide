from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel


class LearningSessionStartRequest(BaseModel):
    goal: int = 10
    semantic_anchor_target: int = 3
    double_recall_target: int = 4
    anti_confusion_target: int = 2
    association_recall_target: int = 1


class LearningSessionItemView(BaseModel):
    item_id: int
    word_id: int
    word_text: str
    quest_type: str
    source_bucket: str | None = None
    position: int
    is_done: bool
    is_correct: bool | None = None
    launch_path: str


class LearningSessionResponse(BaseModel):
    session_id: int
    session_date: date
    goal: int
    status: str
    items: list[LearningSessionItemView]


class LearningSessionCompleteItemRequest(BaseModel):
    correct: bool | None = None
    result_payload: dict[str, Any] | None = None


class LearningSessionCompleteItemResponse(BaseModel):
    item_id: int
    is_done: bool
    is_correct: bool | None
    next_review_at: datetime | None = None
    remaining: int


class LearningSessionSummaryResponse(BaseModel):
    session_id: int
    total: int
    done: int
    correct: int
    incorrect: int
    finished: bool
