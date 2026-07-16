from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.helpers.battle.constants import MATCHMAKING_SEARCH_MAX_AGE_SECONDS
from app.helpers.battle.eligibility import non_test_user_sql_conditions
from app.helpers.datetime_utils import utc_naive_now
from app.models.battle_matchmaking import BattleMatchmakingTicket, MatchmakingStatus
from app.models.user import User


class MatchmakingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_ticket(self, ticket_id: int, user_id: int) -> BattleMatchmakingTicket | None:
        result = await self.db.execute(
            select(BattleMatchmakingTicket).where(
                BattleMatchmakingTicket.id == ticket_id,
                BattleMatchmakingTicket.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def find_opponent_ticket(
        self,
        user_id: int,
        mode: str,
        rating: int,
        *,
        rating_window: int = 5000,
        max_age_seconds: int = MATCHMAKING_SEARCH_MAX_AGE_SECONDS,
    ) -> BattleMatchmakingTicket | None:
        cutoff = utc_naive_now() - timedelta(seconds=max_age_seconds)
        result = await self.db.execute(
            select(BattleMatchmakingTicket)
            .join(User, User.id == BattleMatchmakingTicket.user_id)
            .where(
                BattleMatchmakingTicket.status == MatchmakingStatus.SEARCHING,
                BattleMatchmakingTicket.mode == mode,
                BattleMatchmakingTicket.user_id != user_id,
                BattleMatchmakingTicket.created_at >= cutoff,
                BattleMatchmakingTicket.rating >= rating - rating_window,
                BattleMatchmakingTicket.rating <= rating + rating_window,
                *non_test_user_sql_conditions(),
            )
            .order_by(BattleMatchmakingTicket.created_at.asc())
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        return result.scalar_one_or_none()

    async def create_ticket(
        self,
        user_id: int,
        mode: str,
        rating: int,
    ) -> BattleMatchmakingTicket:
        ticket = BattleMatchmakingTicket(
            user_id=user_id,
            mode=mode,
            rating=rating,
            status=MatchmakingStatus.SEARCHING,
        )
        self.db.add(ticket)
        await self.db.flush()
        return ticket

    async def expire_stale_searching_tickets(self, *, older_than) -> int:
        result = await self.db.execute(
            select(BattleMatchmakingTicket).where(
                BattleMatchmakingTicket.status == MatchmakingStatus.SEARCHING,
                BattleMatchmakingTicket.created_at < older_than,
            )
        )
        count = 0
        for ticket in result.scalars().all():
            ticket.status = MatchmakingStatus.CANCELLED
            count += 1
        return count

    async def cancel_searching_for_user(self, user_id: int) -> None:
        result = await self.db.execute(
            select(BattleMatchmakingTicket).where(
                BattleMatchmakingTicket.user_id == user_id,
                BattleMatchmakingTicket.status == MatchmakingStatus.SEARCHING,
            )
        )
        for ticket in result.scalars().all():
            ticket.status = MatchmakingStatus.CANCELLED
