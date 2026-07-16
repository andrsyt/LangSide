import logging

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, DbSession, Friends, UserCommands
from app.schemas.user import PublicUserProfileResponse, UserResponse, UserUpdate

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/by-public-id/{public_id}", response_model=PublicUserProfileResponse)
async def get_user_by_public_id(
    public_id: int,
    friends: Friends,
) -> PublicUserProfileResponse:
    return await friends.lookup_by_public_id(public_id)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    current_user: CurrentUser,
    user_commands: UserCommands,
) -> UserResponse:
    logger.info(f"Updating user {current_user.id} with data: {user_data.model_dump()}")

    updated_user = await user_commands.update_user(current_user.id, user_data)
    logger.info(
        f"Updated user {updated_user.id}, preferred_language: "
        f"{updated_user.preferred_language}, type: {type(updated_user.preferred_language)}"
    )

    return UserResponse.model_validate(updated_user)


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "Account deleted successfully"},
        422: {"description": "Validation error"},
    },
)
async def delete_current_user(
    current_user: CurrentUser,
    db: DbSession,
    user_commands: UserCommands,
) -> None:
    """
    Delete the current user account.

    After deletion:
    - All user data is removed via cascade (words, sessions, stats)
    - The token becomes invalid

    Note: Deletion confirmation happens on the client (iOS system alert).
    """
    logger.info(f"User {current_user.id} requested account deletion")

    try:
        logger.info(f"Deleting user: id={current_user.id}, email={current_user.email}")
        await user_commands.delete_user(current_user.id)
        logger.info(f"User deleted successfully: id={current_user.id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}",
        )
