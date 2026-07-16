from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SemanticAnchorSession(Base):
    __tablename__ = "semantic_anchor_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    word_id: Mapped[int] = mapped_column(Integer, ForeignKey("words.id", ondelete="CASCADE"), index=True)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    example: Mapped[str] = mapped_column(Text, nullable=False)
    anchor_variants: Mapped[list[Any]] = mapped_column(JSON, nullable=False)
    context_variants: Mapped[list[Any]] = mapped_column(JSON, nullable=False)
    correct_context_index: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime, server_default=func.now())
    used_at: Mapped[object | None] = mapped_column(DateTime, nullable=True)
