from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.public_user_id import PUBLIC_ID_INITIAL, PUBLIC_ID_MAX
from app.models.user_public_id import UserPublicIdCounter


class UserPublicIdRepository:
    """Atomically allocate public_id via a singleton counter."""

    _COUNTER_ROW_ID = 1

    def __init__(self, db: AsyncSession):
        self.db = db

    async def allocate_next(self) -> int:
        result = await self.db.execute(
            select(UserPublicIdCounter)
            .where(UserPublicIdCounter.id == self._COUNTER_ROW_ID)
            .with_for_update()
        )
        counter = result.scalar_one_or_none()
        if counter is None:
            counter = UserPublicIdCounter(
                id=self._COUNTER_ROW_ID,
                next_public_id=PUBLIC_ID_INITIAL,
            )
            self.db.add(counter)
            await self.db.flush()

        assigned = int(counter.next_public_id)
        if assigned > PUBLIC_ID_MAX:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Public ID pool exhausted",
            )

        counter.next_public_id = assigned + 1
        await self.db.flush()
        return assigned
