from __future__ import annotations

from sqlalchemy import Boolean, DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.word import DifficultyLevel


class CommonWord(Base):
    __tablename__ = "common_words"

    id: Mapped[int] = mapped_column(primary_key=True)
    word_text: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    cefr_level: Mapped[DifficultyLevel] = mapped_column(Enum(DifficultyLevel), nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime, server_default=func.now())
    is_everyday_common: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
