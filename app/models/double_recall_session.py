from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.word import Word


class DoubleRecallSession(Base):
    __tablename__ = "double_recall_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    word_id: Mapped[int] = mapped_column(Integer, ForeignKey("words.id", ondelete="CASCADE"), index=True)
    example_sentences: Mapped[list[Any]] = mapped_column(JSON, nullable=False)
    example_neighbor_word_ids: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)
    correct_example_index: Mapped[int] = mapped_column(Integer, nullable=False)
    min_synonyms: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    translation_prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[object] = mapped_column(DateTime, server_default=func.now())
    current_step: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    translation_passed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
    )
    gloss_recall_passed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
    )
    example_passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    own_sentence_passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    own_sentence_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    synonyms_passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    synonyms_submitted: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)
    used_at: Mapped[object | None] = mapped_column(DateTime, nullable=True)

    user: Mapped[User] = relationship("User", back_populates="double_recall_sessions")
    word: Mapped[Word] = relationship("Word", back_populates="double_recall_sessions")
