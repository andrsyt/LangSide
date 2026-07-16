from __future__ import annotations

from datetime import date

from sqlalchemy import Date, DateTime, ForeignKey, Integer, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserDailyActivity(Base):
    """Per-user daily counters for home stats and streaks."""

    __tablename__ = "user_daily_activity"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "activity_date",
            name="uq_user_daily_activity_user_date",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    activity_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    exercises_completed: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
    )
    words_reviewed: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
    )
    words_added: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
    )
    updated_at: Mapped[object] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
