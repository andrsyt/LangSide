"""Unit tests: RevenueCat webhook tier logic."""

from app.models.user import UserTier
from app.services.billing.purchase_service import (
    build_entitlements_from_customer_info,
    has_premium_entitlement,
    is_premium_active_in_entitlements,
    resolve_tier_from_revenuecat_event,
)


def test_has_premium_entitlement_case_insensitive() -> None:
    assert has_premium_entitlement(["Premium"]) is True
    assert has_premium_entitlement(["premium"]) is True
    assert has_premium_entitlement(["pro"]) is False
    assert has_premium_entitlement(None) is False


def test_is_premium_active_in_entitlements_case_insensitive() -> None:
    assert is_premium_active_in_entitlements(
        {"Premium": {"is_active": True}},
    ) is True
    assert is_premium_active_in_entitlements(
        {"premium": {"is_active": False}},
    ) is False


def test_apply_event_initial_purchase_with_entitlement_ids() -> None:
    tier = resolve_tier_from_revenuecat_event(
        "INITIAL_PURCHASE",
        {"entitlement_ids": ["Premium"]},
        current_tier=UserTier.FREE,
    )
    assert tier == UserTier.PREMIUM


def test_apply_event_real_revenuecat_payload_shape() -> None:
    tier = resolve_tier_from_revenuecat_event(
        "RENEWAL",
        {
            "entitlement_id": None,
            "entitlement_ids": ["Premium"],
            "product_id": "dev.langside.annual",
            "app_user_id": "32",
        },
        current_tier=UserTier.FREE,
    )
    assert tier == UserTier.PREMIUM


def test_apply_event_expiration_revokes_premium() -> None:
    tier = resolve_tier_from_revenuecat_event(
        "EXPIRATION",
        {"entitlement_ids": ["Premium"]},
        current_tier=UserTier.PREMIUM,
    )
    assert tier == UserTier.FREE


def test_apply_event_cancellation_keeps_tier_until_expiration() -> None:
    tier = resolve_tier_from_revenuecat_event(
        "CANCELLATION",
        {"entitlement_ids": ["Premium"]},
        current_tier=UserTier.PREMIUM,
    )
    assert tier == UserTier.PREMIUM


def test_build_entitlements_from_customer_info() -> None:
    entitlements = build_entitlements_from_customer_info(
        {
            "customer_info": {
                "entitlements": {
                    "Premium": {"is_active": True},
                },
            },
        },
    )
    assert entitlements["Premium"]["is_active"] is True
