from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_word_confusion import UserWordConfusion


class UserWordConfusionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_pair(
        self,
        user_id: int,
        word_id: int,
        neighbor_word_id: int,
    ) -> UserWordConfusion | None:
        result = await self.db.execute(
            select(UserWordConfusion).where(
                UserWordConfusion.user_id == user_id,
                UserWordConfusion.word_id == word_id,
                UserWordConfusion.neighbor_word_id == neighbor_word_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_top_neighbor_word_id(
        self,
        user_id: int,
        word_id: int,
        allowed_neighbor_ids: set[int],
    ) -> int | None:
        if not allowed_neighbor_ids:
            return None
        result = await self.db.execute(
            select(UserWordConfusion.neighbor_word_id)
            .where(
                UserWordConfusion.user_id == user_id,
                UserWordConfusion.word_id == word_id,
                UserWordConfusion.neighbor_word_id.in_(allowed_neighbor_ids),
            )
            .order_by(UserWordConfusion.weight.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_ranked_word_ids_for_user(
        self,
        user_id: int,
        limit: int,
        exclude_ids: list[int] | None = None,
    ) -> list[int]:
        query = (
            select(UserWordConfusion.word_id)
            .where(UserWordConfusion.user_id == user_id)
            .order_by(
                UserWordConfusion.weight.desc(),
                UserWordConfusion.updated_at.desc(),
            )
        )
        if exclude_ids:
            query = query.where(UserWordConfusion.word_id.notin_(exclude_ids))
        result = await self.db.execute(query)
        ordered_ids: list[int] = []
        for word_id in result.scalars().all():
            if word_id not in ordered_ids:
                ordered_ids.append(word_id)
            if len(ordered_ids) >= limit:
                break
        return ordered_ids

    async def add(self, row: UserWordConfusion) -> UserWordConfusion:
        self.db.add(row)
        return row
