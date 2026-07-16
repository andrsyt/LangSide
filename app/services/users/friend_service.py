from __future__ import annotations

from app.helpers.datetime_utils import utc_naive_now

import secrets

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.public_user_id import is_valid_public_id
from app.models.friendship import FriendInviteCode, Friendship, FriendshipStatus
from app.helpers.battle import enum_value
from app.repository.battle_repository import BattleRepository
from app.repository.friendship_repository import FriendshipRepository
from app.schemas.friend import (
    FriendActionResponse,
    FriendsListResponse,
    FriendView,
)
from app.schemas.user import PublicUserProfileResponse
from app.services.users.user_service import UserQueryService


class FriendService:
    def __init__(self, db: AsyncSession, user_id: int):
        self.db = db
        self.user_id = user_id
        self.friends = FriendshipRepository(db)
        self.battles = BattleRepository(db)
        self.users = UserQueryService(db)

    async def _invite_code(self) -> str:
        existing = await self.friends.get_invite_code(self.user_id)
        if existing is not None:
            return existing.code
        code = secrets.token_urlsafe(6).replace("-", "").upper()[:10]
        row = FriendInviteCode(user_id=self.user_id, code=code)
        await self.friends.save_invite_code(row)
        return code

    async def _friend_view(self, other_id: int, status: FriendshipStatus) -> FriendView | None:
        user = await self.users.find_user_by_id(other_id)
        if user is None:
            return None
        stats = await self.battles.get_stats(other_id)
        return FriendView(
            user_id=other_id,
            public_id=user.public_id,
            username=user.username,
            rating=stats.rating if stats else 1000,
            win_streak=stats.win_streak if stats else 0,
            league=enum_value(stats.league) if stats else "bronze",
            status=enum_value(status),
        )

    async def lookup_by_public_id(self, public_id: int) -> PublicUserProfileResponse:
        if not is_valid_public_id(public_id):
            raise HTTPException(status_code=400, detail="Invalid public ID")
        user = await self.users.get_user_by_public_id(public_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        if user.id == self.user_id:
            raise HTTPException(status_code=400, detail="Cannot add yourself")
        stats = await self.battles.get_stats(user.id)
        return PublicUserProfileResponse(
            public_id=user.public_id,
            username=user.username,
            rating=stats.rating if stats else 1000,
            win_streak=stats.win_streak if stats else 0,
            league=enum_value(stats.league) if stats else "bronze",
        )

    async def list_friends(self) -> FriendsListResponse:
        friendships = await self.friends.list_for_user(self.user_id)
        accepted: list[FriendView] = []
        incoming: list[FriendView] = []
        outgoing: list[FriendView] = []

        for f in friendships:
            other_id = (
                f.addressee_id if f.requester_id == self.user_id else f.requester_id
            )
            view = await self._friend_view(other_id, f.status)
            if view is None:
                continue
            if f.status == FriendshipStatus.ACCEPTED:
                accepted.append(view)
            elif f.status == FriendshipStatus.PENDING:
                if f.addressee_id == self.user_id:
                    incoming.append(view)
                else:
                    outgoing.append(view)

        code = await self._invite_code()
        await self.db.commit()
        return FriendsListResponse(
            friends=accepted,
            pending_incoming=incoming,
            pending_outgoing=outgoing,
            invite_code=code,
        )

    async def send_request(
        self,
        *,
        public_id: int | None = None,
        username: str | None = None,
        invite_code: str | None = None,
    ) -> FriendActionResponse:
        target_id: int | None = None
        if public_id is not None:
            if not is_valid_public_id(public_id):
                raise HTTPException(status_code=400, detail="Invalid public ID")
            user = await self.users.get_user_by_public_id(public_id)
            if user is None:
                raise HTTPException(status_code=404, detail="User not found")
            target_id = user.id
        elif invite_code:
            row = await self.friends.get_by_invite_code(invite_code.strip().upper())
            if row is None:
                raise HTTPException(status_code=404, detail="Invite code not found")
            target_id = row.user_id
        elif username:
            user = await self.users.get_user_by_username(username.strip())
            if user is None:
                raise HTTPException(status_code=404, detail="User not found")
            target_id = user.id
        else:
            raise HTTPException(
                status_code=400,
                detail="public_id, username or invite_code required",
            )

        if target_id == self.user_id:
            raise HTTPException(status_code=400, detail="Cannot add yourself")

        existing = await self.friends.get_between(self.user_id, target_id)
        if existing is not None:
            if existing.status == FriendshipStatus.ACCEPTED:
                return FriendActionResponse(message="Already friends")
            return FriendActionResponse(message="Request already pending")

        friendship = Friendship(
            requester_id=self.user_id,
            addressee_id=target_id,
            status=FriendshipStatus.PENDING,
        )
        await self.friends.create(friendship)
        await self.db.commit()
        return FriendActionResponse(message="Friend request sent")

    async def accept_request(self, friend_user_id: int) -> FriendActionResponse:
        target = await self.friends.get_pending_incoming(
            addressee_id=self.user_id,
            requester_id=friend_user_id,
        )
        if target is None:
            raise HTTPException(status_code=404, detail="Pending request not found")
        target.status = FriendshipStatus.ACCEPTED
        target.accepted_at = utc_naive_now()
        await self.db.commit()
        return FriendActionResponse(message="Friend added")

    async def decline_request(self, friend_user_id: int) -> FriendActionResponse:
        target = await self.friends.get_pending_incoming(
            addressee_id=self.user_id,
            requester_id=friend_user_id,
        )
        if target is None:
            raise HTTPException(status_code=404, detail="Pending request not found")
        await self.friends.delete(target)
        await self.db.commit()
        return FriendActionResponse(message="Request declined")
