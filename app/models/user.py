from __future__ import annotations

import enum

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import TYPE_CHECKING

from app.db.base import Base
from app.models.word import DifficultyLevel

if TYPE_CHECKING:
    from app.models.anti_confusion_session import AntiConfusionSession
    from app.models.double_recall_session import DoubleRecallSession
    from app.models.quest import Quest
    from app.models.refresh_token import RefreshToken
    from app.models.session import Session
    from app.models.training import Training
    from app.models.usage import Usage
    from app.models.user_word_confusion import UserWordConfusion
    from app.models.word import Word
    from app.models.battle import UserBattleStats
    from app.models.friendship import Friendship


class UserTier(str, enum.Enum):
    FREE = "free"
    PREMIUM = "premium"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        index=True,
        nullable=False,
    )
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    tier: Mapped[UserTier] = mapped_column(Enum(UserTier), default=UserTier.FREE)
    preferred_language: Mapped[str | None] = mapped_column(
        String(16),
        nullable=True,
        default=None,
    )
    created_at: Mapped[object] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[object | None] = mapped_column(DateTime, onupdate=func.now(), nullable=True)
    device_hash: Mapped[str | None] = mapped_column(String, unique=True, index=True, nullable=True)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    words: Mapped[list[Word]] = relationship("Word", back_populates="user", cascade="all, delete-orphan")
    usage_records: Mapped[list[Usage]] = relationship("Usage", back_populates="user", cascade="all, delete-orphan")
    sessions: Mapped[list[Session]] = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    quests: Mapped[list[Quest]] = relationship("Quest", back_populates="user", cascade="all, delete-orphan")
    trainings: Mapped[list[Training]] = relationship("Training", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens: Mapped[list[RefreshToken]] = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    anti_confusion_sessions: Mapped[list[AntiConfusionSession]] = relationship(
        "AntiConfusionSession",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    double_recall_sessions: Mapped[list[DoubleRecallSession]] = relationship(
        "DoubleRecallSession",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    word_confusions: Mapped[list[UserWordConfusion]] = relationship(
        "UserWordConfusion",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    battle_stats: Mapped[UserBattleStats | None] = relationship(
        "UserBattleStats",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    friendships_sent: Mapped[list[Friendship]] = relationship(
        "Friendship",
        foreign_keys="Friendship.requester_id",
        back_populates="requester",
        cascade="all, delete-orphan",
    )
    friendships_received: Mapped[list[Friendship]] = relationship(
        "Friendship",
        foreign_keys="Friendship.addressee_id",
        back_populates="addressee",
        cascade="all, delete-orphan",
    )
    english_level: Mapped[DifficultyLevel] = mapped_column(
        Enum(DifficultyLevel),
        nullable=False,
        default=DifficultyLevel.B1,
    )
