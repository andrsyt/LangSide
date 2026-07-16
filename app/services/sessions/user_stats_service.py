from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.session import SessionProgressService
from app.models.word import StudyStatus
from app.repository.learning_session_item_repository import LearningSessionItemRepository
from app.repository.learning_session_repository import LearningSessionRepository
from app.repository.session_item_repository import SessionItemRepository
from app.repository.session_repository import SessionRepository
from app.repository.user_daily_activity_repository import UserDailyActivityRepository
from app.repository.word_repository import WordRepository
from app.schemas.stats import HomeStatsResponse
from app.helpers.datetime_utils import utc_naive_now


class UserStatsService:
    """Records study activity and builds home-screen statistics."""

    def __init__(self, db: AsyncSession, user_id: int):
        self.db = db
        self.user_id = user_id
        self.words = WordRepository(db)
        self.daily = UserDailyActivityRepository(db)
        self.sessions = SessionRepository(db)
        self.session_items = SessionItemRepository(db)
        self.learning_sessions = LearningSessionRepository(db)
        self.learning_session_items = LearningSessionItemRepository(db)

    async def record_exercise_completed(self, when: datetime | None = None) -> None:
        day = (when or utc_naive_now()).date()
        await self.daily.increment(self.user_id, day, exercises=1)

    async def record_word_reviewed(self, when: datetime | None = None) -> None:
        day = (when or utc_naive_now()).date()
        await self.daily.increment(self.user_id, day, reviews=1)

    async def record_word_added(self, when: datetime | None = None) -> None:
        day = (when or utc_naive_now()).date()
        await self.daily.increment(self.user_id, day, words_added=1)

    async def list_study_dates(self) -> list[date]:
        """Any day with real study: exercises, vocab reviews, or new words."""
        dates: set[date] = set()
        dates.update(await self.daily.list_active_dates(self.user_id))
        dates.update(await self._list_exercise_activity_dates())
        return sorted(dates)

    async def _list_exercise_activity_dates(self) -> list[date]:
        session_dates = await self.session_items.list_answered_dates_for_user(
            self.user_id
        )
        learning_dates = await self.learning_session_items.list_completed_dates_for_user(
            self.user_id
        )
        return sorted(set(session_dates) | set(learning_dates))

    def _day_start(self, day: date) -> datetime:
        return datetime(day.year, day.month, day.day)

    async def count_exercises_completed_on(self, day: date) -> int:
        start = self._day_start(day)
        end = start + timedelta(days=1)
        session_count = await self.session_items.count_answered_for_user_between(
            self.user_id,
            start,
            end,
        )
        learning_count = await self.learning_session_items.count_completed_for_user_between(
            self.user_id,
            start,
            end,
        )
        return session_count + learning_count

    async def count_vocab_reviews_on(self, day: date) -> int:
        """Spaced-repetition checks only (not session / mixed exercises)."""
        row = await self.daily.get_for_date(self.user_id, day)
        return int(row.words_reviewed) if row is not None else 0

    async def count_words_added_on(self, day: date) -> int:
        start = self._day_start(day)
        end = start + timedelta(days=1)
        return await self.words.count_created_between(self.user_id, start, end)

    async def count_session_cards_done_today(self, today: date) -> int:
        session = await self.sessions.get_by_user_and_date(self.user_id, today)
        if session is None:
            return 0
        return await self.session_items.count_done_for_session(session.id)

    async def _get_vocabulary_stats(self) -> dict:
        now = utc_naive_now()
        week_from_now = now + timedelta(days=7)
        return {
            "total_words": await self.words.count_for_user(self.user_id),
            "learning_words": await self.words.count_by_status_for_user(
                self.user_id,
                StudyStatus.LEARNING,
            ),
            "mastered_words": await self.words.count_by_status_for_user(
                self.user_id,
                StudyStatus.MASTERED,
            ),
            "words_due_today": await self.words.count_due_for_user_until(
                self.user_id,
                now,
            ),
            "words_due_this_week": await self.words.count_due_for_user_until(
                self.user_id,
                week_from_now,
            ),
        }

    async def get_home_stats(self) -> HomeStatsResponse:
        today = utc_naive_now().date()
        review = await self._get_vocabulary_stats()
        study_dates = await self.list_study_dates()
        current_streak, best_streak = SessionProgressService.compute_streaks(study_dates)

        total = int(review["total_words"])
        mastered = int(review["mastered_words"])
        mastery_percent = int(round(100 * mastered / total)) if total > 0 else 0

        due_today = int(review["words_due_today"])
        due_week = int(review["words_due_this_week"])
        exercises_today = await self.count_exercises_completed_on(today)
        reviews_today = await self.count_vocab_reviews_on(today)
        words_added_today = await self.count_words_added_on(today)
        session_cards_done = await self.count_session_cards_done_today(today)

        return HomeStatsResponse(
            current_streak=current_streak,
            best_streak=best_streak,
            study_days_total=len(set(study_dates)),
            total_words=total,
            learning_words=int(review["learning_words"]),
            mastered_words=mastered,
            words_due_today=due_today,
            words_due_later_this_week=max(0, due_week - due_today),
            mastery_percent=mastery_percent,
            exercises_today=exercises_today,
            reviews_today=reviews_today,
            practice_today=exercises_today + reviews_today,
            words_added_today=words_added_today,
            session_cards_done_today=session_cards_done,
        )
