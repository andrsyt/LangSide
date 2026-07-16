from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class BattleMode(str, enum.Enum):
    QUICK = "quick"
    RANKED = "ranked"
    UNRANKED = "unranked"
    TYPING = "typing"
    VOICE = "voice"
    AI = "ai"


class BattleStatus(str, enum.Enum):
    ACTIVE = "active"
    FINISHED = "finished"
    CANCELLED = "cancelled"


class BattleLeague(str, enum.Enum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    DIAMOND = "diamond"


class UserBattleStats(Base):
    __tablename__ = "user_battle_stats"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1000")
    xp: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    wins: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    losses: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    draws: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    win_streak: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    best_win_streak: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    battles_played: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    league: Mapped[BattleLeague] = mapped_column(
        Enum(BattleLeague, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        server_default=BattleLeague.BRONZE.value,
    )
    weekly_xp: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    season_week: Mapped[str | None] = mapped_column(String(16), nullable=True)
    updated_at: Mapped[object] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped[User] = relationship("User", back_populates="battle_stats")


class Battle(Base):
    __tablename__ = "battles"

    id: Mapped[int] = mapped_column(primary_key=True)
    mode: Mapped[BattleMode] = mapped_column(
        Enum(BattleMode, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )
    status: Mapped[BattleStatus] = mapped_column(
        Enum(BattleStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        server_default=BattleStatus.ACTIVE.value,
    )
    is_ranked: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    round_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="3")
    round_seconds: Mapped[int] = mapped_column(Integer, nullable=False, server_default="15")
    season_week: Mapped[str | None] = mapped_column(String(16), nullable=True, index=True)
    round_deadline_at: Mapped[object | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime, server_default=func.now())
    finished_at: Mapped[object | None] = mapped_column(DateTime, nullable=True)

    participants: Mapped[list[BattleParticipant]] = relationship(
        "BattleParticipant",
        back_populates="battle",
        cascade="all, delete-orphan",
    )
    rounds: Mapped[list[BattleRound]] = relationship(
        "BattleRound",
        back_populates="battle",
        cascade="all, delete-orphan",
        order_by="BattleRound.round_index",
    )


class BattleParticipant(Base):
    __tablename__ = "battle_participants"
    __table_args__ = (
        UniqueConstraint("battle_id", "slot", name="uq_battle_participant_slot"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    battle_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("battles.id", ondelete="CASCADE"),
        index=True,
    )
    user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    slot: Mapped[int] = mapped_column(Integer, nullable=False)
    display_name: Mapped[str] = mapped_column(String(64), nullable=False)
    is_bot: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    rating_before: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rating_after: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    xp_earned: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    is_winner: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    battle: Mapped[Battle] = relationship("Battle", back_populates="participants")


class BattleRound(Base):
    __tablename__ = "battle_rounds"
    __table_args__ = (
        UniqueConstraint("battle_id", "round_index", name="uq_battle_round_index"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    battle_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("battles.id", ondelete="CASCADE"),
        index=True,
    )
    round_index: Mapped[int] = mapped_column(Integer, nullable=False)
    prompt_text: Mapped[str] = mapped_column(Text, nullable=False)
    correct_answer: Mapped[str] = mapped_column(String(255), nullable=False)
    choices_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    player_answer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    player_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    player_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    opponent_answer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    opponent_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    opponent_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    battle: Mapped[Battle] = relationship("Battle", back_populates="rounds")
