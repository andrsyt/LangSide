from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.usage import Usage


class UsageRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user_and_date(self, user_id: int, usage_date: date) -> Usage | None:
        result = await self.db.execute(
            select(Usage).where(Usage.user_id == user_id, Usage.date == usage_date)
        )
        return result.scalar_one_or_none()

    async def get_request_count_for_date(self, user_id: int, usage_date: date) -> int:
        result = await self.db.execute(
            select(Usage.request_count).where(
                Usage.user_id == user_id,
                Usage.date == usage_date,
            )
        )
        return int(result.scalar_one_or_none() or 0)

    async def get_monthly_request_count(
        self,
        user_id: int,
        first_day: date,
        next_month: date,
    ) -> int:
        result = await self.db.execute(
            select(func.sum(Usage.request_count)).where(
                Usage.user_id == user_id,
                Usage.date >= first_day,
                Usage.date < next_month,
            )
        )
        return int(result.scalar_one_or_none() or 0)

    async def create(self, usage: Usage) -> Usage:
        self.db.add(usage)
        return usage
