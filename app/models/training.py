from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.word import Word


class Training(Base):
    __tablename__ = "trainings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    word_id: Mapped[int] = mapped_column(Integer, ForeignKey("words.id", ondelete="CASCADE"), index=True)
    synonyms_shown: Mapped[list[Any]] = mapped_column(JSON, nullable=False)
    synonyms_user: Mapped[list[Any]] = mapped_column(JSON, nullable=False)
    user_association: Mapped[list[Any]] = mapped_column(JSON, nullable=False)
    semantic_anchor_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    freeform_associations: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)
    association_v2_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    association_recall_cue: Mapped[str | None] = mapped_column(String, nullable=True)
    completed_quest_types: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)
    example_sentence: Mapped[str] = mapped_column(String, nullable=False)
    last_training_at: Mapped[object] = mapped_column(DateTime, nullable=False)

    user: Mapped[User] = relationship("User", back_populates="trainings")
    word: Mapped[Word] = relationship("Word", back_populates="trainings")
