"""RevenueCat webhook auth and payload parsing (no DB)."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.core.config import settings
from app.core.exceptions.http import (
    BadRequestError,
    InternalServerError,
    UnauthorizedError,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ParsedRevenueCatWebhook:
    """Normalized webhook payload ready for tier application."""

    event_type: str
    effective_event_type: str
    is_test_event: bool
    user_id: int | None
    app_user_id: object
    event_payload: dict[str, object]
    skip_tier_update: bool
    skip_message: str | None = None


class RevenueCatWebhookParser:
    """Validates auth and extracts user/event data from RevenueCat webhooks."""

    @staticmethod
    def verify_authorization(
        auth_header: str,
        *,
        is_test_event: bool,
    ) -> None:
        secret = settings.REVENUECAT_WEBHOOK_SECRET
        if not secret:
            logger.error("REVENUECAT_WEBHOOK_SECRET is not configured")
            raise InternalServerError(
                "Webhook secret is not configured",
                error_code="WEBHOOK_SECRET_MISSING",
            )

        if auth_header.startswith("Bearer "):
            received = auth_header.removeprefix("Bearer ").strip()
            if received != secret:
                logger.warning("Invalid RevenueCat webhook secret")
                raise UnauthorizedError(
                    "Invalid webhook secret",
                    error_code="WEBHOOK_UNAUTHORIZED",
                )
            return

        if not is_test_event:
            raise UnauthorizedError(
                "Missing or invalid Authorization header",
                error_code="WEBHOOK_UNAUTHORIZED",
            )
        logger.warning("Test event without Authorization header (allowed)")

    @staticmethod
    def parse(
        data: dict[str, object],
        *,
        inject_test_premium: bool = True,
    ) -> ParsedRevenueCatWebhook:
        event_raw = data.get("event")
        if not isinstance(event_raw, dict) or not event_raw:
            raise BadRequestError(
                "Invalid payload structure: Missing 'event' field in payload",
                error_code="WEBHOOK_INVALID_PAYLOAD",
            )

        event_data: dict[str, object] = dict(event_raw)
        event_type = str(event_data.get("type") or "")
        is_test_event = event_type == "TEST"
        app_user_id = event_data.get("app_user_id") or event_data.get(
            "original_app_user_id"
        )
        if not app_user_id:
            raise BadRequestError(
                "Missing app_user_id in event",
                error_code="WEBHOOK_MISSING_USER",
            )

        try:
            user_id = int(app_user_id)  # type: ignore[arg-type]
        except (ValueError, TypeError):
            if is_test_event:
                return ParsedRevenueCatWebhook(
                    event_type=event_type,
                    effective_event_type=event_type,
                    is_test_event=True,
                    user_id=None,
                    app_user_id=app_user_id,
                    event_payload=event_data,
                    skip_tier_update=True,
                    skip_message=(
                        "Test event received (UUID app_user_id, tier update skipped)"
                    ),
                )
            raise BadRequestError(
                f"Invalid app_user_id: {app_user_id}. Expected numeric user_id.",
                error_code="WEBHOOK_INVALID_USER",
            ) from None

        event_payload = dict(event_data)
        if (
            inject_test_premium
            and is_test_event
            and not event_payload.get("entitlement_ids")
            and not event_payload.get("customer_info")
        ):
            event_payload["entitlement_ids"] = ["Premium"]

        effective = "INITIAL_PURCHASE" if is_test_event else event_type
        return ParsedRevenueCatWebhook(
            event_type=event_type,
            effective_event_type=effective,
            is_test_event=is_test_event,
            user_id=user_id,
            app_user_id=app_user_id,
            event_payload=event_payload,
            skip_tier_update=False,
        )
