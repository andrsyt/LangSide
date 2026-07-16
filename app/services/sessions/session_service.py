from __future__ import annotations

from app.helpers.datetime_utils import utc_naive_now

from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.today_session_config import (
    TODAY_EXTEND_BATCH,
    TODAY_SOFT_GOAL,
    TODAY_STREAK_MIN,
    clamp_daily_goal,
)
from app.helpers.today_session_selection import TodaySessionPick, TodaySessionWordPicker
from app.services.sessions.discovery_word_service import DiscoveryWordService
from app.helpers.session import SessionAccessService, SessionProgressService
from app.models.session import Session, SessionItem, SessionStatus
from app.models.word import DifficultyLevel, Word
from app.repository.session_item_repository import SessionItemRepository
from app.repository.session_repository import SessionRepository
from app.repository.user_repository import UserRepository
from app.repository.word_repository import WordRepository
from app.services.sessions.user_stats_service import UserStatsService


class SessionQueryService:
    """Read-only use cases for today sessions."""

    def __init__(self, db: AsyncSession, user_id: int):
        self.db = db
        self.user_id = user_id
        self.sessions = SessionRepository(db)
        self.session_items = SessionItemRepository(db)
        self.session_access = SessionAccessService(db, user_id)
        self.stats = UserStatsService(db, user_id)
        self.discovery = DiscoveryWordService(db, user_id)

    async def get_today_session(self) -> tuple[Session, list[Word]] | None:
        today = utc_naive_now().date()
        session = await self.sessions.get_by_user_and_date(self.user_id, today)
        if session is None:
            return None
        words = await self.session_access.load_session_words(session.id)
        return session, words

    async def get_next_session_card(
        self,
        session_id: int,
    ) -> tuple[SessionItem, Word, int] | None:
        session = await self.session_access.get_session_or_404(session_id)

        if session.status == SessionStatus.FINISHED:
            await self.session_access.reset_session_items(session.id)
            await self.session_access.reshuffle_session_item_positions(session.id)
            session.status = SessionStatus.ACTIVE
            session.finished_at = None
            await self.db.commit()
            await self.db.refresh(session)

        total = await self.session_items.count_for_session(session.id)
        item = await self.session_items.get_next_pending(session.id)
        if item is None:
            await self.session_access.reset_session_items(session.id)
            await self.session_access.reshuffle_session_item_positions(session.id)
            session.status = SessionStatus.ACTIVE
            session.finished_at = None
            await self.db.commit()
            item = await self.session_items.get_next_pending(session.id)
            if item is None:
                return None

        word = await self.session_access.get_word_or_404(item.word_id)
        return item, word, total

    async def get_session_progress(self, session_id: int) -> tuple[int, int]:
        session = await self.session_access.get_session_or_404(session_id)
        total = await self.session_items.count_for_session(session.id)
        done = await self.session_items.count_done_for_session(session.id)
        return done, total

    @staticmethod
    def session_progress_meta(
        session: Session,
        done: int,
        total: int,
    ) -> dict:
        return {
            "recommended_goal": TODAY_SOFT_GOAL,
            "streak_threshold": TODAY_STREAK_MIN,
            "can_extend": session.status != SessionStatus.FINISHED,
            "done": done,
            "total": total,
            "soft_goal_met": done >= TODAY_STREAK_MIN,
        }

    async def get_profile_stats(self) -> dict:
        today = utc_naive_now().date()
        study_dates = await self.stats.list_study_dates()
        today_session = await self.sessions.get_by_user_and_date(self.user_id, today)
        today_done = 0
        if today_session is not None:
            today_done = await self.session_items.count_done_for_session(today_session.id)

        current_streak, best_streak = SessionProgressService.compute_streaks(study_dates)
        today_goal = today_session.goal if today_session is not None else TODAY_SOFT_GOAL
        discovery_remaining = await self.discovery.discovery_slots_remaining(today)
        return {
            "current_streak": current_streak,
            "best_streak": best_streak,
            "study_days_total": len(set(study_dates)),
            "today_done": today_done,
            "today_goal": today_goal,
            "today_recommended_goal": TODAY_SOFT_GOAL,
            "today_streak_threshold": TODAY_STREAK_MIN,
            "today_soft_goal_met": today_done >= TODAY_STREAK_MIN,
            "today_daily_goal_met": (
                today_done >= today_goal if today_session is not None else False
            ),
            "today_discovery_remaining": discovery_remaining,
        }


class SessionCommandService:
    """Write use cases for today sessions."""

    def __init__(self, db: AsyncSession, user_id: int):
        self.db = db
        self.user_id = user_id
        self.sessions = SessionRepository(db)
        self.session_items = SessionItemRepository(db)
        self.words = WordRepository(db)
        self.users = UserRepository(db)
        self.session_access = SessionAccessService(db, user_id)
        self.stats = UserStatsService(db, user_id)

    async def _user_english_level(self) -> DifficultyLevel:
        user = await self.users.get_by_id(self.user_id)
        if user is None:
            return DifficultyLevel.B1
        return user.english_level

    async def start_today_session(
        self,
        daily_goal: int = TODAY_SOFT_GOAL,
    ) -> tuple[Session, list[Word], int]:
        daily_goal = clamp_daily_goal(daily_goal)
        now = utc_naive_now()
        today = now.date()

        session = await self.sessions.get_by_user_and_date(self.user_id, today)
        if session is None:
            session = await self.sessions.create_active(
                user_id=self.user_id,
                session_date=today,
                goal=daily_goal,
            )

        words = await self.session_access.load_session_words(session.id)
        exclude_ids = [word.id for word in words]
        exclude_texts = {word.word_text.strip().lower() for word in words}
        english_level = await self._user_english_level()
        session.goal = daily_goal

        if words and session.status == SessionStatus.FINISHED:
            previous_word_ids = [word.id for word in words]
            await self.session_items.delete_for_session(session.id)
            selection = await TodaySessionWordPicker.pick(
                self.db,
                self.words,
                self.user_id,
                daily_goal,
                now,
                english_level,
                exclude_ids=[],
                session_date=today,
                previous_word_ids=previous_word_ids,
                exclude_texts=exclude_texts,
            )
            to_add = selection.picks
            if to_add:
                await self._attach_picks_to_session(
                    session.id,
                    to_add,
                    start_position=1,
                    when=now,
                )
            session.status = SessionStatus.ACTIVE
            session.finished_at = None
            await self.db.commit()
            await self.db.refresh(session)
            words = await self.session_access.load_session_words(session.id)
            return session, words, selection.skipped_count

        if len(words) >= daily_goal:
            await self.db.commit()
            await self.db.refresh(session)
            return session, words, 0

        need = daily_goal - len(words)
        selection = await TodaySessionWordPicker.pick(
            self.db,
            self.words,
            self.user_id,
            need,
            now,
            english_level,
            exclude_ids=exclude_ids,
            session_date=today,
            exclude_texts=exclude_texts,
        )
        to_add = selection.picks
        if not to_add:
            await self.db.commit()
            await self.db.refresh(session)
            return session, words, selection.skipped_count

        await self._attach_picks_to_session(
            session.id,
            to_add,
            start_position=len(words) + 1,
            when=now,
        )

        if session.status == SessionStatus.FINISHED:
            session.status = SessionStatus.ACTIVE
            session.finished_at = None

        await self.db.commit()
        await self.db.refresh(session)
        combined = await self.session_access.load_session_words(session.id)
        return session, combined, selection.skipped_count

    async def _attach_picks_to_session(
        self,
        session_id: int,
        picks: TodaySessionPick,
        start_position: int,
        when: datetime,
    ) -> None:
        items = [
            SessionItem(
                session_id=session_id,
                word_id=word.id,
                position=start_position + idx,
                source=source,
            )
            for idx, (word, source) in enumerate(picks)
        ]
        await self.session_items.create_many(items)
        await self.words.touch_last_today_session(
            self.user_id,
            [word.id for word, _ in picks],
            when,
        )

    async def extend_session(
        self,
        session_id: int,
        count: int = TODAY_EXTEND_BATCH,
    ) -> tuple[Session, list[Word], int]:
        count = max(1, min(count, TODAY_EXTEND_BATCH * 4))
        session = await self.session_access.get_session_or_404(session_id)
        if session.status == SessionStatus.FINISHED:
            raise HTTPException(
                status_code=400,
                detail="Session already finished; start a new today session",
            )

        today = utc_naive_now().date()
        if session.session_date != today:
            raise HTTPException(
                status_code=400,
                detail="Can only extend today's session",
            )

        words = await self.session_access.load_session_words(session.id)
        exclude_ids = [word.id for word in words]
        exclude_texts = {word.word_text.strip().lower() for word in words}
        english_level = await self._user_english_level()
        now = utc_naive_now()

        selection = await TodaySessionWordPicker.pick(
            self.db,
            self.words,
            self.user_id,
            count,
            now,
            english_level,
            exclude_ids=exclude_ids,
            session_date=today,
            exclude_texts=exclude_texts,
        )
        to_add = selection.picks
        if not to_add:
            raise HTTPException(
                status_code=404,
                detail="No more words available to extend session",
            )

        start_position = await self.session_items.max_position_for_session(session.id) + 1
        await self._attach_picks_to_session(
            session.id,
            to_add,
            start_position=start_position,
            when=now,
        )
        session.goal += len(to_add)

        await self.db.commit()
        await self.db.refresh(session)
        added_words = [word for word, _ in to_add]
        return session, added_words, len(to_add)

    async def submit_session_answer(
        self,
        session_id: int,
        word_id: int,
        is_correct: bool,
        grade: str | None = None,
    ) -> Word:
        session = await self.session_access.get_session_or_404(session_id)
        if session.status == SessionStatus.FINISHED:
            raise HTTPException(status_code=400, detail="Session already finished")

        item = await self.session_access.get_session_item_or_404(session.id, word_id)
        if item.is_done:
            raise HTTPException(status_code=400, detail="Item already answered")

        word = await self.session_access.get_word_or_404(word_id)
        SessionProgressService.apply_review_result(word, is_correct=is_correct)
        item.is_done = True
        item.is_correct = is_correct
        item.grade = grade
        item.answered_at = utc_naive_now()

        await self.stats.record_exercise_completed()
        await self.db.commit()
        await self.db.refresh(word)
        return word

    async def finish_session(self, session_id: int) -> dict:
        session = await self.session_access.get_session_or_404(session_id)
        total = await self.session_items.count_for_session(session.id)
        done = await self.session_items.count_done_for_session(session.id)
        correct = await self.session_items.count_correct_for_session(session.id)

        session.status = SessionStatus.FINISHED
        session.finished_at = utc_naive_now()
        await self.db.commit()
        await self.db.refresh(session)

        return {
            "session_id": session.id,
            "total": total,
            "correct": correct,
            "incorrect": max(0, done - correct),
            "finished": True,
            "streak_threshold": TODAY_STREAK_MIN,
            "soft_goal_met": done >= TODAY_STREAK_MIN,
        }