from __future__ import annotations

import enum
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.word import DifficultyLevel as difficulty_level

if TYPE_CHECKING:
    from app.models.test_session import TestSession
    from app.models.user import User
    from app.models.word import Word


class QuestType(str, enum.Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    FILL_IN_THE_BLANK = "fill_in_the_blank"
    MATCHING = "matching"
    TRUE_FALSE = "true_false"
    ORDERING = "ordering"
    CLASSIFICATION = "classification"
    REARRANGEMENT = "rearrangement"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"
    PROBLEM_SOLVING = "problem_solving"
    RESEARCH = "research"


class Quest(Base):
    __tablename__ = "quests"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    word_id: Mapped[int] = mapped_column(Integer, ForeignKey("words.id", ondelete="CASCADE"), nullable=False)
    quest_type: Mapped[QuestType] = mapped_column(
        Enum(QuestType, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    correct_answer: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[list[Any]] = mapped_column(JSON, nullable=False)
    difficulty: Mapped[difficulty_level] = mapped_column(Enum(difficulty_level), nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    user_answer: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime, server_default=func.now())
    answered_at: Mapped[object | None] = mapped_column(DateTime, nullable=True)
    test_session_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("test_sessions.id", ondelete="CASCADE"), nullable=True, index=True
    )
    round: Mapped[int | None] = mapped_column(Integer, nullable=True)
    question_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_retry: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped[User] = relationship("User", back_populates="quests")
    word: Mapped[Word] = relationship("Word", back_populates="quests")
    test_session: Mapped[Optional[TestSession]] = relationship("TestSession", back_populates="quests")
