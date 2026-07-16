from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.common_word import CommonWord
from app.models.word import DifficultyLevel


class CommonWordRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_word_text(self, word_text: str) -> CommonWord | None:
        result = await self.db.execute(
            select(CommonWord).where(CommonWord.word_text == word_text)
        )
        return result.scalar_one_or_none()

    async def list_words_by_level(
        self,
        level: DifficultyLevel,
        limit: int = 20,
        exclude_words: list[str] | None = None,
    ) -> list[str]:
        query = select(CommonWord.word_text).where(
            CommonWord.cefr_level == level,
            CommonWord.is_everyday_common == True,  # noqa: E712
        )
        if exclude_words:
            query = query.where(CommonWord.word_text.notin_(exclude_words))
        query = query.order_by(CommonWord.word_text.asc()).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def fetch_random_catalog_entries(
        self,
        *,
        limit: int,
        exclude_normalized: set[str] | None = None,
    ) -> list[tuple[str, DifficultyLevel]]:
        """Random slice of the shared catalog (same pool for all players in a battle)."""
        exclude_normalized = exclude_normalized or set()
        fetch_limit = max(limit * 12, limit + 40)
        result = await self.db.execute(
            select(CommonWord.word_text, CommonWord.cefr_level)
            .where(CommonWord.is_everyday_common == True)  # noqa: E712
            .order_by(func.random())
            .limit(fetch_limit)
        )
        rows: list[tuple[str, DifficultyLevel]] = []
        for word_text, level in result.all():
            key = word_text.strip().lower()
            if not key or key in exclude_normalized:
                continue
            rows.append((word_text.strip(), level))
        return rows

    async def is_everyday_common(self, word_text: str) -> bool:
        result = await self.db.execute(
            select(CommonWord.is_everyday_common).where(
                CommonWord.word_text == word_text
            )
        )
        value = result.scalar_one_or_none()
        return bool(value) if value is not None else False

    async def fetch_random_by_levels(
        self,
        levels: list[DifficultyLevel],
        limit: int,
        exclude_normalized: set[str] | None = None,
    ) -> list[tuple[str, DifficultyLevel]]:
        if not levels or limit <= 0:
            return []

        exclude_normalized = exclude_normalized or set()
        fetch_limit = max(limit * 12, limit + 40)
        result = await self.db.execute(
            select(CommonWord.word_text, CommonWord.cefr_level)
            .where(
                CommonWord.cefr_level.in_(levels),
                CommonWord.is_everyday_common == True,  # noqa: E712
            )
            .order_by(func.random())
            .limit(fetch_limit)
        )
        rows: list[tuple[str, DifficultyLevel]] = []
        for word_text, level in result.all():
            key = word_text.strip().lower()
            if not key or key in exclude_normalized:
                continue
            rows.append((word_text.strip(), level))
            if len(rows) >= limit:
                break
        return rows