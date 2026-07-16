from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class FriendshipStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    BLOCKED = "blocked"


class Friendship(Base):
    __tablename__ = "friendships"
    __table_args__ = (
        UniqueConstraint(
            "requester_id",
            "addressee_id",
            name="uq_friendship_pair",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    requester_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    addressee_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    status: Mapped[FriendshipStatus] = mapped_column(
        Enum(FriendshipStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        server_default=FriendshipStatus.PENDING.value,
    )
    created_at: Mapped[object] = mapped_column(DateTime, server_default=func.now())
    accepted_at: Mapped[object | None] = mapped_column(DateTime, nullable=True)

    requester: Mapped[User] = relationship(
        "User",
        foreign_keys=[requester_id],
        back_populates="friendships_sent",
    )
    addressee: Mapped[User] = relationship(
        "User",
        foreign_keys=[addressee_id],
        back_populates="friendships_received",
    )


class FriendInviteCode(Base):
    __tablename__ = "friend_invite_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(12), unique=True, index=True)
    created_at: Mapped[object] = mapped_column(DateTime, server_default=func.now())
