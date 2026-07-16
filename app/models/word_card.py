from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WordCard(Base):
    __tablename__ = "word_cards"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    word_id: Mapped[int] = mapped_column(Integer, ForeignKey("words.id"), nullable=False)
    translation: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    examples: Mapped[list[Any]] = mapped_column(JSON, nullable=False)
    synonyms: Mapped[list[Any]] = mapped_column(JSON, nullable=False)
    associations: Mapped[list[Any]] = mapped_column(JSON, nullable=False)
    semantic_anchor_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    association_v2_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime, server_default=func.now())
