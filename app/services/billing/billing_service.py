from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.billing.rules import BillingRulesService, BillingUsageService
from app.models.usage import Usage
from app.repository.usage_repository import UsageRepository
from app.services.users.user_service import UserQueryService


class BillingService:
    """
    Wrapper service for API limits and usage statistics.
    """

    def __init__(self, db: AsyncSession, user_id: int):
        self.db = db
        self.user_id = user_id
        self.usage = UsageRepository(db)
        self.user_query = UserQueryService(db)
        self.billing_rules = BillingRulesService()
        self.billing_usage = BillingUsageService(db, user_id)

    async def record_api_usage(self) -> Usage:
        today = date.today()
        usage = await self.usage.get_by_user_and_date(self.user_id, today)

        if not usage:
            usage = Usage(user_id=self.user_id, date=today, request_count=1)
            await self.usage.create(usage)
        else:
            usage.request_count += 1

        await self.db.commit()
        await self.db.refresh(usage)
        return usage

    async def check_rate_limits(self) -> bool:
        user = await self.user_query.get_user_by_id(self.user_id)
        limits = self.billing_rules.get_limits(user.tier)

        request_today = await self.billing_usage.get_today_usage_count()
        total_monthly = await self.billing_usage.get_monthly_usage_count()

        return request_today < limits["daily"] and total_monthly < limits["monthly"]