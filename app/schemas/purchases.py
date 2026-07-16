from pydantic import BaseModel
from typing import Optional, Dict


class IOSVerifyRequest(BaseModel):
    mock_token: str | None = None
    transaction_id: str | None = None
    product_id: str | None = None


class IOSVerifyResponse(BaseModel):
    """
    Payload returned to the client.
    """

    ok: bool
    tier: str
    message: str


class RevenueCatEntitlement(BaseModel):
    """RevenueCat entitlement."""
    is_active: bool
    product_identifier: Optional[str] = None
    expires_date: Optional[str] = None
    purchase_date: Optional[str] = None


class RevenueCatCustomerInfo(BaseModel):
    entitlements: Dict[str, RevenueCatEntitlement] = {}


class RevenueCatEvent(BaseModel):
    type: str  
    id: str
    app_user_id: str 
    aliases: list = []
    customer_info: RevenueCatCustomerInfo


class RevenueCatWebhookPayload(BaseModel):
    event: RevenueCatEvent

