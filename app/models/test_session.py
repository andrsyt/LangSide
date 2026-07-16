from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.word import DifficultyLevel

if TYPE_CHECKING:
    from app.models.quest import Quest


class TestSessionStatus(str, enum.Enum):
    IN_PROGRESS = "in_progress"
    ROUND1_COMPLETED = "round1_completed"
    ROUND2_COMPLETED = "round2_completed"
    FINISHED = "finished"


class TestSession(Base):
    __tablename__ = "test_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    difficulty: Mapped[DifficultyLevel] = mapped_column(Enum(DifficultyLevel), nullable=False)
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    round: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[TestSessionStatus] = mapped_column(
        Enum(TestSessionStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=TestSessionStatus.IN_PROGRESS,
    )
    current_question_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[object] = mapped_column(DateTime, server_default=func.now())
    round1_correct_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    round1_incorrect_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    round2_correct_count: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)
    round2_incorrect_count: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)
    round1_completed_at: Mapped[object | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[object | None] = mapped_column(DateTime, nullable=True)

    quests: Mapped[list[Quest]] = relationship("Quest", back_populates="test_session", cascade="all, delete-orphan")
