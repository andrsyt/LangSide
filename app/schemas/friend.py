from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from app.core.public_user_id import PUBLIC_ID_MAX, PUBLIC_ID_MIN


class FriendView(BaseModel):
    """Friend or request: internal user_id for accept/decline, public_id for UI."""

    user_id: int
    public_id: int = Field(..., ge=PUBLIC_ID_MIN, le=PUBLIC_ID_MAX)
    username: str
    rating: int
    win_streak: int
    league: str
    status: str


class FriendsListResponse(BaseModel):
    friends: list[FriendView]
    pending_incoming: list[FriendView]
    pending_outgoing: list[FriendView]
    invite_code: str | None = Field(
        None,
        description="Legacy invite link; iOS uses public_id",
    )


class FriendRequestBody(BaseModel):
    public_id: int | None = Field(
        None,
        ge=PUBLIC_ID_MIN,
        le=PUBLIC_ID_MAX,
        description="8-digit public account ID",
    )
    username: str | None = None
    invite_code: str | None = None

    @model_validator(mode="after")
    def require_lookup_field(self) -> FriendRequestBody:
        if self.public_id is None and not self.username and not self.invite_code:
            raise ValueError("One of public_id, username or invite_code is required")
        return self


class FriendActionResponse(BaseModel):
    ok: bool = True
    message: str
