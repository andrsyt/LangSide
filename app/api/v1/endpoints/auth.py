import hashlib
import logging
import secrets
import uuid

from fastapi import APIRouter, Form, HTTPException, status

from app.api.deps import (
    RefreshTokens,
    UserIdentity,
    UserQueries,
    UserRegistration,
)
from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.user import (
    AnonymousLoginRequest,
    LogoutRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
)
from app.services.users.refresh_token_service import RefreshTokenService

router = APIRouter()
logger = logging.getLogger(__name__)
debug_logger = logging.getLogger("debug")


async def _token_response(
    refresh_tokens: RefreshTokenService,
    user: User,
) -> TokenResponse:
    """Access JWT + new opaque refresh (stored in DB as a hash)."""
    access_token = create_access_token(data={"sub": str(user.id)})
    expires_in_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    refresh_raw = await refresh_tokens.issue_refresh_token(user.id)
    return TokenResponse(
        access_token=access_token,
        token_type="Bearer",
        expires_in=expires_in_seconds,
        refresh_token=refresh_raw,
    )


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    registration: UserRegistration,
) -> UserResponse:
    """
    Register a new user.

    Accepts:
    - email: user email
    - username: username
    - password: password
    - preferred_language: UI language (optional, default None)
    """
    debug_logger.warning("🔥 REGISTER ENDPOINT CALLED 🔥")
    debug_logger.warning(
        f"🔥 REGISTER: email={user_data.email}, username={user_data.username}, "
        f"password_len={len(user_data.password)}"
    )

    try:
        logger.info(
            f"Registration attempt: email={user_data.email}, username={user_data.username}, "
            f"preferred_language={user_data.preferred_language}"
        )
        debug_logger.warning("🔥 REGISTER: calling create_user")
        new_user = await registration.create_user(user_data)
        debug_logger.warning(f"🔥 REGISTER: SUCCESS! user_id={new_user.id}")
        logger.info(f"User registered successfully: id={new_user.id}, email={new_user.email}")
        return UserResponse.model_validate(new_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}",
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    user_queries: UserQueries,
    refresh_tokens: RefreshTokens,
    email: str = Form(),
    password: str = Form(),
) -> TokenResponse:
    user = await user_queries.get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    if not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    return await _token_response(refresh_tokens, user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access(
    body: RefreshTokenRequest,
    refresh_tokens: RefreshTokens,
) -> TokenResponse:
    """
    Issue a new access JWT without a password. The old refresh token is one-time
    (marked revoked in DB); response includes a new access + refresh pair.
    """
    user = await refresh_tokens.consume_refresh_token(body.refresh_token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    return await _token_response(refresh_tokens, user)


@router.post("/anonymous", response_model=TokenResponse)
async def anonymous_login(
    body: AnonymousLoginRequest,
    user_queries: UserQueries,
    user_identity: UserIdentity,
    refresh_tokens: RefreshTokens,
) -> TokenResponse:
    installation_id = body.installation_id.strip()
    if not installation_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Installation ID is required",
        )
    device_hash = hashlib.sha256(
        f"{installation_id}:{settings.ANON_SALT}".encode("utf-8")
    ).hexdigest()

    anon_id = uuid.uuid4().hex
    user = await user_queries.get_user_by_device_hash(device_hash)

    if user:
        return await _token_response(refresh_tokens, user)
    user = await user_identity.create_anonymous_user(
        email=f"anon_{anon_id}@guest.local",
        username=f"anon_{anon_id[:12]}",
        device_hash=device_hash,
        hashed_password=hash_password(secrets.token_urlsafe(32)),
    )
    return await _token_response(refresh_tokens, user)


@router.post("/logout", response_model=None)
async def logout(
    body: LogoutRequest,
    refresh_tokens: RefreshTokens,
) -> dict[str, bool]:
    await refresh_tokens.revoke_refresh_token(body.refresh_token)
    return {"ok": True}
