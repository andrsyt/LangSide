from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.friendship import FriendInviteCode, Friendship, FriendshipStatus


class FriendshipRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_between(self, user_a: int, user_b: int) -> Friendship | None:
        result = await self.db.execute(
            select(Friendship).where(
                or_(
                    (Friendship.requester_id == user_a) & (Friendship.addressee_id == user_b),
                    (Friendship.requester_id == user_b) & (Friendship.addressee_id == user_a),
                )
            )
        )
        return result.scalar_one_or_none()

    async def delete(self, friendship: Friendship) -> None:
        await self.db.delete(friendship)
        await self.db.flush()

    async def create(self, friendship: Friendship) -> Friendship:
        self.db.add(friendship)
        await self.db.flush()
        return friendship

    async def list_for_user(self, user_id: int) -> list[Friendship]:
        result = await self.db.execute(
            select(Friendship).where(
                or_(
                    Friendship.requester_id == user_id,
                    Friendship.addressee_id == user_id,
                )
            )
        )
        return list(result.scalars().all())

    async def get_pending_incoming(
        self,
        addressee_id: int,
        requester_id: int,
    ) -> Friendship | None:
        """Pending friend request from ``requester_id`` to ``addressee_id``."""
        result = await self.db.execute(
            select(Friendship).where(
                Friendship.addressee_id == addressee_id,
                Friendship.requester_id == requester_id,
                Friendship.status == FriendshipStatus.PENDING,
            )
        )
        return result.scalar_one_or_none()

    async def get_invite_code(self, user_id: int) -> FriendInviteCode | None:
        result = await self.db.execute(
            select(FriendInviteCode).where(FriendInviteCode.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_invite_code(self, code: str) -> FriendInviteCode | None:
        result = await self.db.execute(
            select(FriendInviteCode).where(FriendInviteCode.code == code.upper())
        )
        return result.scalar_one_or_none()

    async def save_invite_code(self, row: FriendInviteCode) -> FriendInviteCode:
        self.db.add(row)
        await self.db.flush()
        return row

    async def friend_user_ids(self, user_id: int) -> list[int]:
        friendships = await self.list_for_user(user_id)
        ids: list[int] = []
        for f in friendships:
            if f.status != FriendshipStatus.ACCEPTED:
                continue
            other = f.addressee_id if f.requester_id == user_id else f.requester_id
            ids.append(other)
        return ids
