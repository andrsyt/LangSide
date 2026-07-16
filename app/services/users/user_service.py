from sqlalchemy.ext.asyncio import AsyncSession

from app.services.users.user_access import (
    UserAccessService,
    UserLanguageSyncService,
    UserValidationService,
)
from app.services.users.language_invalidation import (
    UserLanguageSessionInvalidationService,
)
from app.models.user import User
from app.repository.user_repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate
from app.services.users.user_identity_service import UserIdentityService


class UserQueryService:
    """Read-only use cases for users."""

    def __init__(self, db: AsyncSession):
        self.users = UserRepository(db)
        self.user_access = UserAccessService(db)

    async def get_user_by_id(self, user_id: int) -> User | None:
        return await self.user_access.get_user_or_404(user_id)

    async def find_user_by_id(self, user_id: int) -> User | None:
        return await self.users.get_by_id(user_id)

    async def get_user_by_email(self, user_email: str) -> User | None:
        return await self.users.get_by_email(user_email)

    async def get_user_by_username(self, username: str) -> User | None:
        return await self.users.get_by_username(username)

    async def get_user_by_public_id(self, public_id: int) -> User | None:
        return await self.users.get_by_public_id(public_id)

    async def get_user_by_email_or_username(self, identifier: str) -> User | None:
        return await self.users.get_by_email_or_username(identifier)

    async def get_user_by_device_hash(self, device_hash: str) -> User | None:
        return await self.users.get_by_device_hash(device_hash)


class UserRegistrationService:
    """Handles user registration flow."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.identity = UserIdentityService(db)

    async def create_user(self, user: UserCreate) -> User:
        return await self.identity.create_registered_user(user)


class UserCommandService:
    """Handles user mutations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.users = UserRepository(db)
        self.user_access = UserAccessService(db)
        self.user_validation = UserValidationService(db)
        self.language_sync = UserLanguageSyncService(db)
        self.language_invalidation = UserLanguageSessionInvalidationService(db)

    async def update_user(self, user_id: int, user_data: UserUpdate) -> User:
        user = await self.user_access.get_user_or_404(user_id)

        if user_data.email is not None:
            await self.user_validation.ensure_email_is_unique(
                user_data.email,
                exclude_user_id=user.id,
            )
            user.email = user_data.email
        if user_data.username is not None:
            await self.user_validation.ensure_username_is_unique(
                user_data.username,
                exclude_user_id=user.id,
            )
            user.username = user_data.username

        old_lang = user.preferred_language

        language_changed = (
            user_data.preferred_language is not None
            and user_data.preferred_language != old_lang
        )
        if user_data.preferred_language is not None:
            user.preferred_language = user_data.preferred_language

        if user_data.english_level is not None:
            user.english_level = user_data.english_level

        if language_changed and user.preferred_language is not None:
            await self.language_sync.sync_word_translations_for_user(
                user.id,
                user.preferred_language,
            )
            await self.language_invalidation.invalidate_for_user(user.id)

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete_user(self, user_id: int) -> None:
        user = await self.user_access.get_user_or_404(user_id)
        await self.users.delete_user(user)
        await self.db.commit()
