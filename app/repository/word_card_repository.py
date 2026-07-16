from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.word_card import WordCard


class WordCardRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user_and_word(self, user_id: int, word_id: int) -> WordCard | None:
        result = await self.db.execute(
            select(WordCard).where(
                WordCard.user_id == user_id,
                WordCard.word_id == word_id,
            )
        )
        return result.scalar_one_or_none()

    async def add(self, word_card: WordCard) -> WordCard:
        self.db.add(word_card)
        return word_card
