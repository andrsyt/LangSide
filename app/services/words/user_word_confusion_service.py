
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_word_confusion import UserWordConfusion
from app.repository.user_word_confusion_repository import UserWordConfusionRepository
from app.helpers.datetime_utils import utc_naive_now


class UserWordConfusionQueryService:
    """Read-only use cases for user word confusion pairs."""

    def __init__(self, db: AsyncSession):
        self.confusions = UserWordConfusionRepository(db)

    async def get_top_neighbor_word_id(
        self,
        user_id: int,
        word_id: int,
        allowed_neighbor_ids: set[int],
    ) -> int | None:
        return await self.confusions.get_top_neighbor_word_id(
            user_id=user_id,
            word_id=word_id,
            allowed_neighbor_ids=allowed_neighbor_ids,
        )


class UserWordConfusionCommandService:
    """Write use cases for user word confusion pairs."""

    def __init__(self, db: AsyncSession):
        self.confusions = UserWordConfusionRepository(db)

    async def bump_user_word_confusion(
        self,
        user_id: int,
        word_id: int,
        neighbor_word_id: int | None,
    ) -> None:
        if neighbor_word_id is None or neighbor_word_id == word_id:
            return

        row = await self.confusions.get_pair(
            user_id=user_id,
            word_id=word_id,
            neighbor_word_id=neighbor_word_id,
        )
        if row is None:
            await self.confusions.add(
                UserWordConfusion(
                    user_id=user_id,
                    word_id=word_id,
                    neighbor_word_id=neighbor_word_id,
                    weight=1.0,
                )
            )
            return

        row.weight = float(row.weight) + 1.0
        row.updated_at = utc_naive_now()


async def get_top_neighbor_word_id(
    db: AsyncSession,
    user_id: int,
    word_id: int,
    allowed_neighbor_ids: set[int],
) -> int | None:
    return await UserWordConfusionQueryService(db).get_top_neighbor_word_id(
        user_id=user_id,
        word_id=word_id,
        allowed_neighbor_ids=allowed_neighbor_ids,
    )


async def bump_user_word_confusion(
    db: AsyncSession,
    user_id: int,
    word_id: int,
    neighbor_word_id: int | None,
) -> None:
    await UserWordConfusionCommandService(db).bump_user_word_confusion(
        user_id=user_id,
        word_id=word_id,
        neighbor_word_id=neighbor_word_id,
    )
