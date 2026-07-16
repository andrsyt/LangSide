from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_daily_activity import UserDailyActivity


class UserDailyActivityRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_for_date(
        self,
        user_id: int,
        activity_date: date,
    ) -> UserDailyActivity | None:
        result = await self.db.execute(
            select(UserDailyActivity).where(
                UserDailyActivity.user_id == user_id,
                UserDailyActivity.activity_date == activity_date,
            )
        )
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        user_id: int,
        activity_date: date,
    ) -> UserDailyActivity:
        row = await self.get_for_date(user_id, activity_date)
        if row is not None:
            return row
        row = UserDailyActivity(
            user_id=user_id,
            activity_date=activity_date,
            exercises_completed=0,
            words_reviewed=0,
            words_added=0,
        )
        self.db.add(row)
        await self.db.flush()
        return row

    async def increment(
        self,
        user_id: int,
        activity_date: date,
        *,
        exercises: int = 0,
        reviews: int = 0,
        words_added: int = 0,
    ) -> UserDailyActivity:
        row = await self.get_or_create(user_id, activity_date)
        if exercises:
            row.exercises_completed += exercises
        if reviews:
            row.words_reviewed += reviews
        if words_added:
            row.words_added += words_added
        return row

    async def list_active_dates(self, user_id: int) -> list[date]:
        result = await self.db.execute(
            select(UserDailyActivity.activity_date)
            .where(
                UserDailyActivity.user_id == user_id,
                (
                    (UserDailyActivity.exercises_completed > 0)
                    | (UserDailyActivity.words_reviewed > 0)
                    | (UserDailyActivity.words_added > 0)
                ),
            )
            .order_by(UserDailyActivity.activity_date.asc())
        )
        return [row[0] for row in result.all()]

    async def get_today_row(
        self,
        user_id: int,
        activity_date: date,
    ) -> UserDailyActivity | None:
        return await self.get_for_date(user_id, activity_date)
