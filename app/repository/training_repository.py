from app.helpers.datetime_utils import utc_naive_now

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.training import Training


class TrainingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user_and_word(self, user_id: int, word_id: int) -> Training | None:
        result = await self.db.execute(
            select(Training).where(
                Training.user_id == user_id,
                Training.word_id == word_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_or_create(self, user_id: int, word_id: int) -> Training:
        training = await self.get_by_user_and_word(user_id, word_id)
        if training is None:
            training = Training(
                user_id=user_id,
                word_id=word_id,
                synonyms_shown=[],
                synonyms_user=[],
                user_association=[],
                freeform_associations=[],
                completed_quest_types=[],
                example_sentence="",
                last_training_at=utc_naive_now(),
            )
            self.db.add(training)
            await self.db.flush()
        return training

    async def list_association_recall_word_ids(
        self,
        user_id: int,
        limit: int,
        exclude_word_ids: list[int] | None = None,
    ) -> list[int]:
        query = (
            select(Training.word_id)
            .where(
                Training.user_id == user_id,
                Training.association_v2_data.is_not(None),
                Training.association_recall_cue.is_not(None),
            )
            .order_by(Training.last_training_at.desc())
        )
        if exclude_word_ids:
            query = query.where(Training.word_id.notin_(exclude_word_ids))
        result = await self.db.execute(query)
        return list(result.scalars().all()[:limit])

    async def list_recent_for_user(self, user_id: int, limit: int = 50) -> list[Training]:
        result = await self.db.execute(
            select(Training)
            .where(Training.user_id == user_id)
            .order_by(Training.last_training_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
