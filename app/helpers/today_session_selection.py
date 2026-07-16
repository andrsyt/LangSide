"""Word selection and ordering for today (daily) sessions."""

from __future__ import annotations

import math
import random
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.today_session_config import (
    SESSION_SOURCE_DISCOVERY,
    SESSION_SOURCE_DUE,
    SESSION_SOURCE_LEARNING,
)
from app.helpers.text_utils import is_acceptable_translation
from app.models.word import DifficultyLevel, Word
from app.repository.word_repository import WordRepository
from app.services.sessions.discovery_word_service import DiscoveryWordService

OWN_WORD_RATIO = 0.65

TodaySessionPick = list[tuple[Word, str]]


@dataclass(frozen=True)
class TodaySessionSelection:
    """Result of building a today session: chosen words + how many were filtered out."""

    picks: TodaySessionPick
    skipped_count: int

    @property
    def sources_breakdown(self) -> dict[str, int]:
        return dict(Counter(source for _, source in self.picks))


class TodaySessionWordPicker:
    """Builds a varied word set for a today session run."""

    @staticmethod
    async def pick(
        db: AsyncSession,
        word_repo: WordRepository,
        user_id: int,
        goal: int,
        now: datetime,
        user_english_level: DifficultyLevel,
        exclude_ids: list[int],
        session_date: date,
        previous_word_ids: list[int] | None = None,
        exclude_texts: set[str] | None = None,
    ) -> TodaySessionSelection:
        if goal <= 0:
            return TodaySessionSelection(picks=[], skipped_count=0)

        own_goal = min(goal, max(1, math.ceil(goal * OWN_WORD_RATIO)))
        discovery_goal = max(0, goal - own_goal)

        own_picks = await TodaySessionWordPicker._pick_own_words(
            word_repo=word_repo,
            user_id=user_id,
            goal=own_goal,
            now=now,
            exclude_ids=exclude_ids,
            previous_word_ids=previous_word_ids,
        )

        discovery_picks: TodaySessionPick = []
        if discovery_goal > 0:
            discovery = DiscoveryWordService(db, user_id)
            own_ids = [word.id for word, _ in own_picks]
            discovery_words = await discovery.pick_discovery_words(
                user_level=user_english_level,
                count=discovery_goal,
                session_date=session_date,
                exclude_word_ids=list(exclude_ids) + own_ids,
                exclude_texts=exclude_texts,
            )
            discovery_picks = [
                (word, SESSION_SOURCE_DISCOVERY) for word in discovery_words
            ]

        candidates = own_picks + discovery_picks
        filtered, skipped = TodaySessionWordPicker._apply_quality_filter(candidates)
        final = TodaySessionWordPicker._finalize_picks(
            filtered,
            goal,
            previous_word_ids,
        )
        return TodaySessionSelection(picks=final, skipped_count=skipped)

    @staticmethod
    def _apply_quality_filter(
        picks: TodaySessionPick,
    ) -> tuple[TodaySessionPick, int]:
        """Drop words whose translation fails the quality rules; count how many."""
        kept: TodaySessionPick = []
        skipped = 0
        for word, source in picks:
            if is_acceptable_translation(word.translation, word.word_text):
                kept.append((word, source))
            else:
                skipped += 1
        return kept, skipped

    @staticmethod
    async def _pick_own_words(
        word_repo: WordRepository,
        user_id: int,
        goal: int,
        now: datetime,
        exclude_ids: list[int],
        previous_word_ids: list[int] | None,
    ) -> TodaySessionPick:
        if goal <= 0:
            return []

        due_words = await word_repo.list_due_for_user(
            user_id=user_id,
            now=now,
            limit=goal,
            exclude_ids=exclude_ids or None,
            require_translation=True,
            random_order=True,
        )
        picks: TodaySessionPick = [
            (word, SESSION_SOURCE_DUE) for word in due_words
        ]
        exclude = list(exclude_ids) + [word.id for word, _ in picks]

        remaining = max(0, goal - len(picks))
        if remaining > 0:
            pool_limit = max(remaining * 4, goal * 2, 12)
            learning_words = await word_repo.list_learning_words(
                user_id=user_id,
                limit=pool_limit,
                exclude_ids=exclude or None,
                require_translation=True,
                rotate_by_today=True,
            )
            picks.extend(
                (word, SESSION_SOURCE_LEARNING) for word in learning_words
            )

        return TodaySessionWordPicker._finalize_picks(picks, goal, previous_word_ids)

    @staticmethod
    def _finalize_picks(
        picks: TodaySessionPick,
        goal: int,
        previous_word_ids: list[int] | None,
    ) -> TodaySessionPick:
        if not picks:
            return []

        previous = set(previous_word_ids or [])
        if previous:
            fresh = [item for item in picks if item[0].id not in previous]
            stale = [item for item in picks if item[0].id in previous]
            random.shuffle(fresh)
            random.shuffle(stale)
            ordered = fresh + stale
        else:
            ordered = list(picks)
            random.shuffle(ordered)

        seen: set[int] = set()
        unique: TodaySessionPick = []
        for word, source in ordered:
            if word.id in seen:
                continue
            seen.add(word.id)
            unique.append((word, source))
            if len(unique) >= goal:
                break
        return unique
