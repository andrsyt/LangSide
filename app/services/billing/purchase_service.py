from __future__ import annotations

from datetime import UTC, datetime

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions.http import (
    BadGatewayError,
    NotImplementedAPIError,
    UnauthorizedError,
)
from app.models.user import UserTier
from app.repository.purchase_repository import PurchaseRepository
from app.services.billing.rules import PurchaseAccessService

PREMIUM_ENTITLEMENT = "premium"

_GRANT_TIER_EVENTS = frozenset({
    "INITIAL_PURCHASE",
    "RENEWAL",
    "UNCANCELLATION",
    "NON_RENEWING_PURCHASE",
    "PRODUCT_CHANGE",
    "SUBSCRIPTION_EXTENDED",
})

_REVOKE_TIER_EVENTS = frozenset({
    "EXPIRATION",
})


def has_premium_entitlement(entitlement_ids: list[object] | None) -> bool:
    """Return True when RevenueCat event lists the Premium entitlement."""
    if not entitlement_ids:
        return False
    for item in entitlement_ids:
        if isinstance(item, str) and item.strip().lower() == PREMIUM_ENTITLEMENT:
            return True
    return False


def is_premium_active_in_entitlements(entitlements: dict[str, object]) -> bool:
    """Return True when customer_info entitlements mark Premium as active."""
    for key, data in entitlements.items():
        if not isinstance(key, str) or not isinstance(data, dict):
            continue
        if key.strip().lower() != PREMIUM_ENTITLEMENT:
            continue
        if data.get("is_active", False):
            return True
    return False


def build_entitlements_from_customer_info(event_data: dict[str, object]) -> dict[str, dict[str, object]]:
    """Parse optional customer_info.entitlements block from a webhook event."""
    customer_info = event_data.get("customer_info")
    if not isinstance(customer_info, dict):
        return {}

    raw_entitlements = customer_info.get("entitlements")
    if not isinstance(raw_entitlements, dict):
        return {}

    entitlements_dict: dict[str, dict[str, object]] = {}
    for key, entitlement in raw_entitlements.items():
        if not isinstance(key, str) or not isinstance(entitlement, dict):
            continue
        entitlements_dict[key] = {
            "is_active": entitlement.get("is_active", False),
            "product_identifier": entitlement.get("product_identifier"),
            "expires_date": entitlement.get("expires_date"),
            "purchase_date": entitlement.get("purchase_date"),
        }
    return entitlements_dict


def _is_subscriber_entitlement_active(entitlement: dict[str, object]) -> bool:
    """Return True when a RevenueCat subscriber entitlement is currently active."""
    expires = entitlement.get("expires_date")
    if not expires or not isinstance(expires, str):
        return True
    try:
        expires_dt = datetime.fromisoformat(expires.replace("Z", "+00:00"))
    except ValueError:
        return False
    return expires_dt > datetime.now(UTC)


def build_entitlements_from_subscriber(subscriber: dict[str, object]) -> dict[str, dict[str, object]]:
    """Parse entitlements block from RevenueCat Subscriber API response."""
    raw_entitlements = subscriber.get("entitlements")
    if not isinstance(raw_entitlements, dict):
        return {}

    entitlements_dict: dict[str, dict[str, object]] = {}
    for key, entitlement in raw_entitlements.items():
        if not isinstance(key, str) or not isinstance(entitlement, dict):
            continue
        entitlements_dict[key] = {
            "is_active": _is_subscriber_entitlement_active(entitlement),
            "product_identifier": entitlement.get("product_identifier"),
            "expires_date": entitlement.get("expires_date"),
            "purchase_date": entitlement.get("purchase_date"),
        }
    return entitlements_dict


def resolve_tier_from_revenuecat_event(
    event_type: str,
    event_data: dict[str, object],
    *,
    current_tier: UserTier,
) -> UserTier:
    """Pure tier resolution used by webhook handling and unit tests."""
    entitlement_ids = event_data.get("entitlement_ids")
    if entitlement_ids is None:
        legacy_id = event_data.get("entitlement_id")
        entitlement_ids = [legacy_id] if legacy_id else []

    entitlements_dict = build_entitlements_from_customer_info(event_data)
    premium_in_event = has_premium_entitlement(
        entitlement_ids if isinstance(entitlement_ids, list) else None,
    )

    if event_type in _GRANT_TIER_EVENTS and premium_in_event:
        return UserTier.PREMIUM
    if event_type in _REVOKE_TIER_EVENTS and premium_in_event:
        return UserTier.FREE
    if entitlements_dict:
        return (
            UserTier.PREMIUM
            if is_premium_active_in_entitlements(entitlements_dict)
            else UserTier.FREE
        )
    return current_tier


class SubscriptionService:
    """Сервис для работы с подписками и покупками (iOS / RevenueCat)."""

    def __init__(self, db: AsyncSession, user_id: int):
        self.db = db
        self.user_id = user_id
        self.purchase = PurchaseRepository(db)
        self.purchase_access = PurchaseAccessService(db, user_id)

    async def verify_ios_purchase(self, mock_token: str | None = None) -> UserTier:
        """Верификация покупки iOS. Пока реализован mock-режим/disabled."""
        user = await self.purchase_access.get_user_or_404()

        if settings.IOS_IAP_MODE == "disabled":
            return user.tier

        if settings.IOS_IAP_MODE == "mock":
            if not settings.IOS_IAP_MOCK_TOKEN or mock_token != settings.IOS_IAP_MOCK_TOKEN:
                raise UnauthorizedError(
                    "Invalid mock token",
                    error_code="INVALID_MOCK_TOKEN",
                )

            user.tier = UserTier.PREMIUM
            await self.purchase.save_user(user)
            await self.db.commit()
            await self.db.refresh(user)
            return user.tier

        raise NotImplementedAPIError(
            "Apple purchase verification is not implemented yet",
            error_code="APPLE_VERIFY_NOT_IMPLEMENTED",
        )

    async def restore_purchases(self) -> UserTier:
        """Sync tier from RevenueCat when API key is configured, else return current tier."""
        user = await self.purchase_access.get_user_or_404()
        if not settings.REVENUECAT_API_KEY:
            return user.tier

        entitlements = await self._fetch_subscriber_entitlements()
        new_tier = (
            UserTier.PREMIUM
            if is_premium_active_in_entitlements(entitlements)
            else UserTier.FREE
        )
        if new_tier == user.tier:
            return user.tier

        user.tier = new_tier
        await self.purchase.save_user(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user.tier

    async def _fetch_subscriber_entitlements(self) -> dict[str, dict[str, object]]:
        """Fetch current entitlements for app user from RevenueCat Subscriber API."""
        url = f"https://api.revenuecat.com/v1/subscribers/{self.user_id}"
        headers = {
            "Authorization": f"Bearer {settings.REVENUECAT_API_KEY}",
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise BadGatewayError(
                "Failed to fetch subscription status from RevenueCat",
                error_code="REVENUECAT_FETCH_FAILED",
            ) from exc

        payload = response.json()
        subscriber = payload.get("subscriber")
        if not isinstance(subscriber, dict):
            return {}
        return build_entitlements_from_subscriber(subscriber)

    async def update_tier_from_revenuecat(self, entitlements: dict[str, object]) -> UserTier:
        """Обновить tier по customer_info entitlements (legacy / test payloads)."""
        user = await self.purchase_access.get_user_or_404()
        user.tier = (
            UserTier.PREMIUM
            if is_premium_active_in_entitlements(entitlements)
            else UserTier.FREE
        )
        await self.purchase.save_user(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user.tier

    async def apply_revenuecat_event(
        self,
        event_type: str,
        event_data: dict[str, object],
    ) -> UserTier:
        """Apply tier changes from a RevenueCat webhook event."""
        user = await self.purchase_access.get_user_or_404()
        new_tier = resolve_tier_from_revenuecat_event(
            event_type,
            event_data,
            current_tier=user.tier,
        )
        if new_tier == user.tier:
            return user.tier

        user.tier = new_tier
        await self.purchase.save_user(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user.tier
