from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.quest import Quest
    from app.models.training import Training
    from app.models.user import User
    from app.models.anti_confusion_session import AntiConfusionSession
    from app.models.double_recall_session import DoubleRecallSession


class DifficultyLevel(str, enum.Enum):
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"


class StudyStatus(str, enum.Enum):
    """Word study status."""
    LEARNING = "learning"
    MASTERED = "mastered"


class Word(Base):
    __tablename__ = "words"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    word_text: Mapped[str] = mapped_column(String, nullable=False, index=True)
    translation: Mapped[str | None] = mapped_column(Text, nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    examples: Mapped[str | None] = mapped_column(Text, nullable=True)
    difficulty: Mapped[DifficultyLevel | None] = mapped_column(Enum(DifficultyLevel), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[object | None] = mapped_column(DateTime, onupdate=func.now(), nullable=True)

    is_selected_for_test: Mapped[bool] = mapped_column(Boolean, default=False)
    study_status: Mapped[str | None] = mapped_column(
        Enum(StudyStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=True,
        default=StudyStatus.LEARNING.value,
    )
    knowledge_level: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)
    last_reviewed_at: Mapped[object | None] = mapped_column(DateTime, nullable=True)
    next_review_at: Mapped[object | None] = mapped_column(DateTime, nullable=True)
    review_count: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)
    correct_count: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)
    incorrect_count: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)
    ease_factor: Mapped[float | None] = mapped_column(Float, nullable=True, default=2.5)
    last_today_session_at: Mapped[object | None] = mapped_column(DateTime, nullable=True)

    user: Mapped[User] = relationship("User", back_populates="words")
    quests: Mapped[list[Quest]] = relationship("Quest", back_populates="word", cascade="all, delete-orphan")
    trainings: Mapped[list[Training]] = relationship("Training", back_populates="word", cascade="all, delete-orphan")
    anti_confusion_sessions: Mapped[list[AntiConfusionSession]] = relationship(
        "AntiConfusionSession",
        back_populates="word",
        cascade="all, delete-orphan",
    )
    double_recall_sessions: Mapped[list[DoubleRecallSession]] = relationship(
        "DoubleRecallSession",
        back_populates="word",
        cascade="all, delete-orphan",
    )
