from fastapi import APIRouter

from app.api.deps import Friends
from app.schemas.friend import FriendActionResponse, FriendRequestBody, FriendsListResponse

router = APIRouter()


@router.get("", response_model=FriendsListResponse)
async def list_friends(friends: Friends) -> FriendsListResponse:
    return await friends.list_friends()


@router.post("/request", response_model=FriendActionResponse)
async def send_friend_request(
    body: FriendRequestBody,
    friends: Friends,
) -> FriendActionResponse:
    return await friends.send_request(
        public_id=body.public_id,
        username=body.username,
        invite_code=body.invite_code,
    )


@router.post("/{friend_user_id}/accept", response_model=FriendActionResponse)
async def accept_friend(
    friend_user_id: int,
    friends: Friends,
) -> FriendActionResponse:
    return await friends.accept_request(friend_user_id)


@router.post("/{friend_user_id}/decline", response_model=FriendActionResponse)
async def decline_friend(
    friend_user_id: int,
    friends: Friends,
) -> FriendActionResponse:
    return await friends.decline_request(friend_user_id)
