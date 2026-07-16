from __future__ import annotations

import enum

from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.word import Word


class SessionStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    FINISHED = "FINISHED"


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)

    session_date: Mapped[object] = mapped_column(Date, index=True)

    goal: Mapped[int] = mapped_column(Integer, nullable=False, default=8)

    status: Mapped[SessionStatus] = mapped_column(Enum(SessionStatus), nullable=False, default=SessionStatus.ACTIVE)

    created_at: Mapped[object] = mapped_column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    finished_at: Mapped[object | None] = mapped_column(DateTime, nullable=True)

    user: Mapped[User] = relationship("User", back_populates="sessions")
    items: Mapped[list[SessionItem]] = relationship(
        "SessionItem",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="SessionItem.position",
    )


class SessionItem(Base):
    __tablename__ = "session_items"
    __table_args__ = (
        UniqueConstraint("session_id", "word_id", name="uq_session_items_session_word"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), index=True)
    word_id: Mapped[int] = mapped_column(Integer, ForeignKey("words.id", ondelete="CASCADE"), index=True)

    position: Mapped[int] = mapped_column(Integer, nullable=False)

    is_done: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    grade: Mapped[str | None] = mapped_column(String, nullable=True)
    answered_at: Mapped[object | None] = mapped_column(DateTime, nullable=True)
    source: Mapped[str | None] = mapped_column(String(32), nullable=True)

    session: Mapped[Session] = relationship("Session", back_populates="items")
    word: Mapped[Word] = relationship("Word")
