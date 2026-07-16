from __future__ import annotations

import enum

from typing import Any

from sqlalchemy import JSON, Boolean, Date, DateTime, Enum, ForeignKey, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class LearningSessionStatus(str, enum.Enum):
    ACTIVE = "active"
    FINISHED = "finished"


class LearningQuestType(str, enum.Enum):
    SEMANTIC_ANCHOR = "semantic_anchor"
    DOUBLE_RECALL = "double_recall"
    ANTI_CONFUSION = "anti_confusion"
    ASSOCIATION_RECALL = "association_recall"


class LearningSession(Base):
    __tablename__ = "learning_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    session_date: Mapped[object] = mapped_column(Date, index=True)
    goal: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    status: Mapped[LearningSessionStatus] = mapped_column(
        Enum(
            LearningSessionStatus,
            name="learningsessionstatus",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=LearningSessionStatus.ACTIVE,
    )
    created_at: Mapped[object] = mapped_column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    finished_at: Mapped[object | None] = mapped_column(DateTime, nullable=True)

    items: Mapped[list["LearningSessionItem"]] = relationship(
        "LearningSessionItem",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="LearningSessionItem.position",
    )


class LearningSessionItem(Base):
    __tablename__ = "learning_session_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    learning_session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("learning_sessions.id", ondelete="CASCADE"), index=True
    )
    word_id: Mapped[int] = mapped_column(Integer, ForeignKey("words.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    quest_type: Mapped[LearningQuestType] = mapped_column(
        Enum(
            LearningQuestType,
            name="learningquesttype",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
    )
    source_bucket: Mapped[str | None] = mapped_column(String, nullable=True)
    is_done: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    result_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    completed_at: Mapped[object | None] = mapped_column(DateTime, nullable=True)

    session: Mapped[LearningSession] = relationship("LearningSession", back_populates="items")
