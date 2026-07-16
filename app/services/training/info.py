from __future__ import annotations

import asyncio

from localization.get_synonyms import get_synonyms_with_auto_fill

from app.schemas.training import WordIntroInfo
from app.services.training.base import TrainingBaseService


class TrainingInfoQueryService(TrainingBaseService):
    """Read-only use cases for training info and metadata."""

    async def get_synonyms_for_word(self, word_id: int) -> list[str]:
        word = await self.get_word(word_id)
        return await asyncio.to_thread(get_synonyms_with_auto_fill, word.word_text)

    async def show_info_about_word(self, word_id: int) -> WordIntroInfo:
        return await self.build_word_intro_info(word_id)
