from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.helpers.battle.eligibility import non_test_user_sql_conditions
from app.helpers.datetime_utils import utc_naive_now
from app.models.battle import (
    Battle,
    BattleParticipant,
    BattleRound,
    BattleStatus,
    UserBattleStats,
)
from app.models.user import User


class BattleRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_stats(self, user_id: int) -> UserBattleStats | None:
        result = await self.db.execute(
            select(UserBattleStats).where(UserBattleStats.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_stats(self, user_id: int) -> UserBattleStats:
        row = UserBattleStats(user_id=user_id)
        self.db.add(row)
        await self.db.flush()
        return row

    async def get_active_battle_for_user(self, user_id: int) -> Battle | None:
        result = await self.db.execute(
            select(Battle)
            .join(BattleParticipant, BattleParticipant.battle_id == Battle.id)
            .where(
                BattleParticipant.user_id == user_id,
                Battle.status == BattleStatus.ACTIVE,
            )
            .order_by(Battle.created_at.desc())
            .limit(1)
            .options(
                selectinload(Battle.participants),
                selectinload(Battle.rounds),
            )
        )
        return result.scalar_one_or_none()

    async def cancel_stale_active_battles(
        self,
        user_id: int,
        *,
        older_than: datetime,
    ) -> int:
        result = await self.db.execute(
            select(Battle)
            .join(BattleParticipant, BattleParticipant.battle_id == Battle.id)
            .where(
                BattleParticipant.user_id == user_id,
                Battle.status == BattleStatus.ACTIVE,
                Battle.created_at < older_than,
            )
            .options(selectinload(Battle.participants))
        )
        count = 0
        now = utc_naive_now()
        for battle in result.scalars().unique().all():
            battle.status = BattleStatus.CANCELLED
            battle.finished_at = now
            count += 1
        return count

    async def get_battle_for_user(
        self,
        battle_id: int,
        user_id: int,
    ) -> Battle | None:
        result = await self.db.execute(
            select(Battle)
            .join(BattleParticipant, BattleParticipant.battle_id == Battle.id)
            .where(
                Battle.id == battle_id,
                BattleParticipant.user_id == user_id,
            )
            .options(
                selectinload(Battle.participants),
                selectinload(Battle.rounds),
            )
        )
        return result.scalar_one_or_none()

    async def create_battle(self, battle: Battle) -> Battle:
        self.db.add(battle)
        await self.db.flush()
        return battle

    async def add_participant(self, participant: BattleParticipant) -> BattleParticipant:
        self.db.add(participant)
        await self.db.flush()
        return participant

    async def add_rounds(self, rounds: list[BattleRound]) -> None:
        self.db.add_all(rounds)
        await self.db.flush()

    async def leaderboard(
        self,
        *,
        limit: int = 50,
        user_ids: list[int] | None = None,
        order_by_weekly: bool = False,
    ) -> list[tuple[UserBattleStats, str]]:
        query = (
            select(UserBattleStats, User.username)
            .join(User, User.id == UserBattleStats.user_id)
        )
        if user_ids is not None:
            if not user_ids:
                return []
            query = query.where(UserBattleStats.user_id.in_(user_ids))
        for condition in non_test_user_sql_conditions():
            query = query.where(condition)
        if order_by_weekly:
            query = query.order_by(
                UserBattleStats.weekly_xp.desc(),
                UserBattleStats.rating.desc(),
            )
        else:
            query = query.order_by(
                UserBattleStats.rating.desc(),
                UserBattleStats.xp.desc(),
            )
        query = query.limit(limit)
        result = await self.db.execute(query)
        return list(result.all())

    async def count_rank_above_rating(self, rating: int) -> int:
        result = await self.db.execute(
            select(func.count(UserBattleStats.id)).where(
                UserBattleStats.rating > rating
            )
        )
        return int(result.scalar() or 0)

    async def recent_correct_answers_for_users(
        self,
        user_ids: list[int],
        *,
        limit: int = 200,
    ) -> list[str]:
        if not user_ids:
            return []
        result = await self.db.execute(
            select(BattleRound.correct_answer)
            .join(Battle, Battle.id == BattleRound.battle_id)
            .join(BattleParticipant, BattleParticipant.battle_id == Battle.id)
            .where(BattleParticipant.user_id.in_(user_ids))
            .order_by(Battle.created_at.desc(), BattleRound.round_index.asc())
            .limit(limit)
        )
        seen: set[str] = set()
        out: list[str] = []
        for row in result.scalars().all():
            key = row.strip().lower()
            if key and key not in seen:
                seen.add(key)
                out.append(row.strip())
        return out
