from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserTier
from app.repository.base import BaseRepository
from app.schemas.user import UserCreate, UserUpdate


class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, User)

    async def get_by_id(self, user_id: int) -> User | None:
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_active_by_id(self, user_id: int) -> User | None:
        query = select(User).where(User.id == user_id, User.is_active == True)  # noqa: E712
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        query = select(User).where(User.username == username)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_public_id(self, public_id: int) -> User | None:
        query = select(User).where(User.public_id == public_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_email_or_username(self, identifier: str) -> User | None:
        query = select(User).where(
            or_(User.email == identifier, User.username == identifier)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_device_hash(self, device_hash: str) -> User | None:
        query = select(User).where(User.device_hash == device_hash)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_user(self, user: User) -> User:
        self.db.add(user)
        return user

    async def delete_user(self, user: User) -> None:
        await self.db.delete(user)

    async def update_tier(self, user: User, tier: UserTier) -> User:
        user.tier = tier
        self.db.add(user)
        return user

    async def get_preferred_language(self, user_id: int):
        query = select(User.preferred_language).where(User.id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
