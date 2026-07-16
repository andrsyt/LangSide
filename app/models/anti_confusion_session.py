from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.word import Word


class AntiConfusionSession(Base):
    __tablename__ = "anti_confusion_session"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    word_id: Mapped[int] = mapped_column(Integer, ForeignKey("words.id", ondelete="CASCADE"), index=True)
    options: Mapped[list[Any]] = mapped_column(JSON, nullable=False)
    option_word_ids: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)
    correct_index: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime, server_default=func.now())
    used_at: Mapped[object | None] = mapped_column(DateTime, nullable=True)

    user: Mapped[User] = relationship("User", back_populates="anti_confusion_sessions")
    word: Mapped[Word] = relationship("Word", back_populates="anti_confusion_sessions")
