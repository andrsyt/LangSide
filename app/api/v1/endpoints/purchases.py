"""
Purchase / subscription endpoints.

Minimal MVP:
- POST /ios/verify  -> upgrades tier to PREMIUM in mock mode
- POST /ios/restore -> return current tier
- POST /webhook -> RevenueCat webhook for automatic tier updates
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Request

from app.api.deps import DbSession, Subscriptions
from app.core.exceptions.base_exception import AppBaseException
from app.core.exceptions.http import BadRequestError, InternalServerError
from app.schemas.purchases import IOSVerifyRequest, IOSVerifyResponse
from app.services.billing.purchase_service import SubscriptionService
from app.services.billing.revenuecat_webhook import RevenueCatWebhookParser

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/ios/verify", response_model=IOSVerifyResponse)
async def ios_verify_endpoint(
    payload: IOSVerifyRequest,
    subscriptions: Subscriptions,
) -> IOSVerifyResponse:
    tier = await subscriptions.verify_ios_purchase(
        mock_token=payload.mock_token,
    )
    return IOSVerifyResponse(ok=True, tier=tier.value, message="Tier updated")


@router.post("/ios/restore", response_model=IOSVerifyResponse)
async def ios_restore_endpoint(
    subscriptions: Subscriptions,
) -> IOSVerifyResponse:
    tier = await subscriptions.restore_purchases()
    return IOSVerifyResponse(ok=True, tier=tier.value, message="Tier restored")


@router.get("/webhook")
async def webhook_test() -> dict[str, object]:
    """Test GET endpoint to verify webhook availability."""
    return {
        "status": "ok",
        "message": "Webhook endpoint is accessible",
        "endpoint": "/api/v1/purchases/webhook",
        "methods": ["GET", "POST"],
    }


@router.post("/webhook")
async def revenuecat_webhook(
    request: Request,
    db: DbSession,
) -> dict[str, object]:
    """Apply RevenueCat subscription events to the user tier."""
    try:
        data = await request.json()
    except Exception as exc:
        logger.error("RevenueCat webhook: Failed to parse JSON: %s", exc)
        raise BadRequestError(
            "Invalid JSON payload",
            error_code="WEBHOOK_INVALID_JSON",
        ) from exc

    if not isinstance(data, dict):
        raise BadRequestError(
            "Invalid JSON payload",
            error_code="WEBHOOK_INVALID_JSON",
        )

    logger.info("RevenueCat webhook received: %s", data)
    event_raw = data.get("event") if isinstance(data.get("event"), dict) else {}
    event_type = str(event_raw.get("type") or "")
    is_test_event = event_type == "TEST"

    RevenueCatWebhookParser.verify_authorization(
        request.headers.get("Authorization", ""),
        is_test_event=is_test_event,
    )
    parsed = RevenueCatWebhookParser.parse(data)

    if parsed.skip_tier_update:
        logger.warning(
            "RevenueCat webhook: Test event with UUID app_user_id: %s. Skipping.",
            parsed.app_user_id,
        )
        return {
            "ok": True,
            "event_type": parsed.event_type,
            "app_user_id": parsed.app_user_id,
            "message": parsed.skip_message,
            "note": (
                "For test events with UUID, tier update is skipped. "
                "Real events must use numeric user_id."
            ),
        }

    assert parsed.user_id is not None
    logger.info(
        "RevenueCat webhook: Processing event '%s' for user %s",
        parsed.effective_event_type,
        parsed.user_id,
    )
    try:
        tier = await SubscriptionService(db, parsed.user_id).apply_revenuecat_event(
            parsed.effective_event_type,
            parsed.event_payload,
        )
    except AppBaseException:
        raise
    except Exception as exc:
        logger.error("RevenueCat webhook: Failed to update user tier: %s", exc)
        raise InternalServerError(
            f"Failed to update user tier: {exc}",
            error_code="WEBHOOK_TIER_UPDATE_FAILED",
        ) from exc

    logger.info(
        "RevenueCat webhook: Updated user %s tier to %s",
        parsed.user_id,
        tier.value,
    )
    return {
        "ok": True,
        "event_type": parsed.event_type,
        "user_id": parsed.user_id,
        "tier": tier.value,
        "message": f"Tier updated to {tier.value} based on entitlements",
    }
