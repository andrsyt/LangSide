"""Loads candidate words for mixed learning sessions through repositories."""

from __future__ import annotations


from sqlalchemy.ext.asyncio import AsyncSession

from app.models.word import Word
from app.repository.training_repository import TrainingRepository
from app.helpers.datetime_utils import utc_naive_now
from app.repository.user_word_confusion_repository import (
    UserWordConfusionRepository,
)
from app.repository.word_repository import WordRepository


class LearningSessionSelectionService:
    """Loads candidate words for mixed learning sessions through repositories."""

    def __init__(self, db: AsyncSession, user_id: int):
        self.user_id = user_id
        self.words = WordRepository(db)
        self.trainings = TrainingRepository(db)
        self.confusions = UserWordConfusionRepository(db)

    async def pick_new_words(
        self,
        limit: int,
        exclude_ids: list[int],
    ) -> list[Word]:
        if limit <= 0:
            return []
        return await self.words.list_learning_words(
            user_id=self.user_id,
            limit=limit,
            exclude_ids=exclude_ids,
            only_unreviewed=True,
        )

    async def pick_any_learning_words(
        self,
        limit: int,
        exclude_ids: list[int],
    ) -> list[Word]:
        """Any learning words — used when strict buckets (unreviewed/due/confusion) are empty."""
        if limit <= 0:
            return []
        return await self.words.list_learning_words(
            user_id=self.user_id,
            limit=limit,
            exclude_ids=exclude_ids,
            only_unreviewed=False,
        )

    async def pick_due_words(
        self,
        limit: int,
        exclude_ids: list[int],
    ) -> list[Word]:
        if limit <= 0:
            return []
        return await self.words.list_due_for_user(
            user_id=self.user_id,
            now=utc_naive_now(),
            limit=limit,
            exclude_ids=exclude_ids,
        )

    async def pick_confusion_words(
        self,
        limit: int,
        exclude_ids: list[int],
    ) -> list[Word]:
        if limit <= 0:
            return []
        ordered_ids = await self.confusions.list_ranked_word_ids_for_user(
            user_id=self.user_id,
            limit=limit,
            exclude_ids=exclude_ids,
        )
        if not ordered_ids:
            return []
        words = await self.words.list_by_ids_for_user(self.user_id, ordered_ids)
        words_by_id = {word.id: word for word in words}
        return [words_by_id[word_id] for word_id in ordered_ids if word_id in words_by_id]

    async def pick_association_recall_words(
        self,
        limit: int,
        exclude_ids: list[int],
    ) -> list[Word]:
        if limit <= 0:
            return []
        word_ids = await self.trainings.list_association_recall_word_ids(
            user_id=self.user_id,
            limit=limit,
            exclude_word_ids=exclude_ids,
        )
        if not word_ids:
            return []
        words = await self.words.list_by_ids_for_user(self.user_id, word_ids)
        words_by_id = {word.id: word for word in words}
        return [words_by_id[word_id] for word_id in word_ids if word_id in words_by_id]
