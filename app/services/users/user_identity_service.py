from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from app.helpers.english_level import parse_english_level
from app.models.word import DifficultyLevel
from app.core.security import hash_password
from app.services.users.user_access import UserValidationService
from app.models.user import User
from app.repository.user_public_id_repository import UserPublicIdRepository
from app.schemas.user import UserCreate


class UserIdentityService:
    """Create users and assign public_id in a single transaction."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.public_ids = UserPublicIdRepository(db)
        self.user_validation = UserValidationService(db)

    async def _next_public_id(self) -> int:
        return await self.public_ids.allocate_next()

    async def create_registered_user(self, data: UserCreate) -> User:
        await self.user_validation.ensure_email_is_unique(data.email)
        await self.user_validation.ensure_username_is_unique(data.username)
        public_id = await self._next_public_id()
        user = User(
            email=data.email,
            username=data.username,
            hashed_password=hash_password(data.password),
            preferred_language=data.preferred_language,
            public_id=public_id,
            english_level=parse_english_level(data.english_level) or DifficultyLevel.B1,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def create_anonymous_user(
        self,
        *,
        email: str,
        username: str,
        device_hash: str,
        hashed_password: str,
    ) -> User:
        public_id = await self._next_public_id()
        user = User(
            email=email,
            username=username,
            hashed_password=hashed_password,
            is_anonymous=True,
            device_hash=device_hash,
            public_id=public_id,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
