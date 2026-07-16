from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class UserWordConfusion(Base):
    __tablename__ = "user_word_confusion"
    __table_args__ = (
        UniqueConstraint("user_id", "word_id", "neighbor_word_id", name="uq_user_word_confusion_pair"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    word_id: Mapped[int] = mapped_column(Integer, ForeignKey("words.id", ondelete="CASCADE"), index=True)
    neighbor_word_id: Mapped[int] = mapped_column(Integer, ForeignKey("words.id", ondelete="CASCADE"), index=True)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    updated_at: Mapped[object | None] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    user: Mapped[User] = relationship("User", back_populates="word_confusions")
