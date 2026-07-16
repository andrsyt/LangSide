from __future__ import annotations

import random

from sqlalchemy.ext.asyncio import AsyncSession

from app.helpers.battle.constants import (
    CEFR_BATTLE_WEIGHTS,
    CHOICES_PER_ROUND,
    FALLBACK_WORDS,
    ROUNDS_MAX,
    ROUNDS_MIN,
)
from app.helpers.battle.text import normalize_answer
from app.models.word import DifficultyLevel
from app.repository.common_word_repository import CommonWordRepository


class BattleRoundPoolBuilder:
    """
    Builds identical battle rounds for all participants from the global
    common-word catalog (weighted random; harder CEFR levels are rarer).
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.common_words = CommonWordRepository(db)

    async def build_rounds(self, count: int) -> list[dict]:
        needed = count + CHOICES_PER_ROUND
        catalog = await self.common_words.fetch_random_catalog_entries(limit=needed)
        pool = self._weighted_sample_unique(catalog, needed)

        if len(pool) < needed:
            seen = {normalize_answer(item["answer"]) for item in pool}
            extra_rows = await self.common_words.fetch_random_catalog_entries(
                limit=needed * 2,
                exclude_normalized=seen,
            )
            pool.extend(
                self._weighted_sample_unique(extra_rows, needed - len(pool))
            )

        if len(pool) < count:
            for fallback in FALLBACK_WORDS:
                key = normalize_answer(fallback["answer"])
                if key not in {normalize_answer(item["answer"]) for item in pool}:
                    pool.append(
                        {
                            "prompt": fallback["prompt"],
                            "answer": fallback["answer"],
                            "level": DifficultyLevel.A2,
                        }
                    )
                if len(pool) >= needed:
                    break

        selected = pool[:count]
        answer_pool = pool
        return [
            {
                "prompt": item["prompt"],
                "answer": item["answer"],
                "choices": self._make_choices(item["answer"], answer_pool),
            }
            for item in selected
        ]

    @staticmethod
    def pick_round_count() -> int:
        return random.randint(ROUNDS_MIN, ROUNDS_MAX)

    def _weighted_sample_unique(
        self,
        rows: list[tuple[str, DifficultyLevel]],
        count: int,
    ) -> list[dict[str, str]]:
        """Sample unique words; CEFR weight makes harder levels less frequent."""
        candidates = list(rows)
        selected: list[dict[str, str]] = []
        seen: set[str] = set()

        while len(selected) < count and candidates:
            weights = [
                CEFR_BATTLE_WEIGHTS.get(level, 0.5) for _, level in candidates
            ]
            index = random.choices(range(len(candidates)), weights=weights, k=1)[0]
            word_text, level = candidates.pop(index)
            key = normalize_answer(word_text)
            if key in seen:
                continue
            seen.add(key)
            selected.append({"prompt": word_text, "answer": word_text, "level": level})

        return selected

    @staticmethod
    def _make_choices(correct: str, pool: list[dict[str, str]]) -> list[str]:
        correct_norm = normalize_answer(correct)
        distractors: list[str] = []
        shuffled = list(pool)
        random.shuffle(shuffled)
        for item in shuffled:
            candidate = item["answer"].strip()
            if normalize_answer(candidate) == correct_norm:
                continue
            if candidate in distractors:
                continue
            distractors.append(candidate)
            if len(distractors) >= CHOICES_PER_ROUND - 1:
                break

        for fallback in FALLBACK_WORDS:
            if len(distractors) >= CHOICES_PER_ROUND - 1:
                break
            candidate = fallback["answer"]
            if normalize_answer(candidate) != correct_norm and candidate not in distractors:
                distractors.append(candidate)

        choices = distractors[: CHOICES_PER_ROUND - 1] + [correct.strip()]
        random.shuffle(choices)
        return choices[:CHOICES_PER_ROUND]
