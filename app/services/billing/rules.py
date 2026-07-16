"""Billing limits, usage counts, and purchase-domain user access."""

from __future__ import annotations

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions.http import ForbiddenError, NotFoundError
from app.models.user import User, UserTier
from app.repository.purchase_repository import PurchaseRepository
from app.repository.usage_repository import UsageRepository


class PurchaseAccessService:
    """Provides purchase-domain access helpers."""

    def __init__(self, db: AsyncSession, user_id: int):
        self.user_id = user_id
        self.purchase = PurchaseRepository(db)
        self._user: User | None = None

    async def get_user_or_404(self) -> User:
        if self._user is None:
            self._user = await self.purchase.get_user(self.user_id)
            if self._user is None:
                raise NotFoundError("User not found", error_code="USER_NOT_FOUND")
        return self._user


class BillingRulesService:
    """Contains billing rules and limits."""

    @staticmethod
    def get_limits(tier: UserTier) -> dict[str, int]:
        is_free = tier == UserTier.FREE
        return {
            "daily": settings.FREE_TIER_DAILY_LIMIT
            if is_free
            else settings.PREMIUM_TIER_DAILY_LIMIT,
            "monthly": settings.FREE_TIER_MONTHLY_LIMIT
            if is_free
            else settings.PREMIUM_TIER_MONTHLY_LIMIT,
        }

    @staticmethod
    def ensure_can_add_word(user: User, word_count: int) -> None:
        if user.tier == UserTier.FREE and word_count >= settings.FREE_TIER_WORD_LIMIT:
            limit = settings.FREE_TIER_WORD_LIMIT
            raise ForbiddenError(
                f"Free plan includes up to {limit} words. "
                "Upgrade to Premium for unlimited words.",
                error_code="WORD_LIMIT_REACHED",
            )

    @staticmethod
    def ensure_can_start_mixed_practice(user: User) -> None:
        if user.tier == UserTier.FREE:
            raise ForbiddenError(
                "Mixed Practice is a Premium feature. Upgrade to unlock it.",
                error_code="MIXED_PRACTICE_PREMIUM",
            )


class BillingUsageService:
    """Provides reusable usage-count helpers for billing."""

    def __init__(self, db: AsyncSession, user_id: int):
        self.user_id = user_id
        self.usage = UsageRepository(db)

    async def get_today_usage_count(self) -> int:
        return await self.usage.get_request_count_for_date(self.user_id, date.today())

    async def get_monthly_usage_count(self) -> int:
        today = date.today()
        first_day = date(today.year, today.month, 1)
        next_month = (
            date(today.year, today.month + 1, 1)
            if today.month < 12
            else date(today.year + 1, 1, 1)
        )
        return await self.usage.get_monthly_request_count(
            user_id=self.user_id,
            first_day=first_day,
            next_month=next_month,
        )
