from __future__ import annotations

import enum

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MatchmakingStatus(str, enum.Enum):
    SEARCHING = "searching"
    MATCHED = "matched"
    CANCELLED = "cancelled"
    AI_STARTED = "ai_started"


class BattleMatchmakingTicket(Base):
    __tablename__ = "battle_matchmaking_tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    mode: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False, default=1000)
    status: Mapped[MatchmakingStatus] = mapped_column(
        Enum(MatchmakingStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        server_default=MatchmakingStatus.SEARCHING.value,
        index=True,
    )
    opponent_user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    battle_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("battles.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[object] = mapped_column(DateTime, server_default=func.now())
    matched_at: Mapped[object | None] = mapped_column(DateTime, nullable=True)
