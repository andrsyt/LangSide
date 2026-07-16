from datetime import date, datetime
import random

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.today_session_config import SESSION_SOURCE_DISCOVERY
from app.models.session import Session, SessionItem


class SessionItemRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_session_and_word(
        self,
        session_id: int,
        word_id: int,
    ) -> SessionItem | None:
        result = await self.db.execute(
            select(SessionItem).where(
                SessionItem.session_id == session_id,
                SessionItem.word_id == word_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_next_pending(self, session_id: int) -> SessionItem | None:
        result = await self.db.execute(
            select(SessionItem)
            .where(
                SessionItem.session_id == session_id,
                SessionItem.is_done == False,  # noqa: E712
            )
            .order_by(SessionItem.position.asc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_for_session(self, session_id: int) -> list[SessionItem]:
        result = await self.db.execute(
            select(SessionItem)
            .where(SessionItem.session_id == session_id)
            .order_by(SessionItem.position.asc())
        )
        return result.scalars().all()

    async def create_many(self, items: list[SessionItem]) -> list[SessionItem]:
        self.db.add_all(items)
        return items

    async def reset_for_session(self, session_id: int) -> None:
        """Clear answer state so the session can be replayed."""
        items = await self.list_for_session(session_id)
        for item in items:
            item.is_done = False
            item.is_correct = None
            item.grade = None
            item.answered_at = None

    async def reshuffle_positions(self, session_id: int) -> None:
        """Randomize item order; no-op when fewer than two cards."""
        items = await self.list_for_session(session_id)
        if len(items) < 2:
            return
        positions = list(range(1, len(items) + 1))
        random.shuffle(positions)
        for item, position in zip(items, positions):
            item.position = position

    async def delete_for_session(self, session_id: int) -> None:
        await self.db.execute(
            delete(SessionItem).where(SessionItem.session_id == session_id)
        )

    async def max_position_for_session(self, session_id: int) -> int:
        result = await self.db.execute(
            select(func.max(SessionItem.position)).where(
                SessionItem.session_id == session_id
            )
        )
        return int(result.scalar() or 0)

    async def count_for_session(self, session_id: int) -> int:
        result = await self.db.execute(
            select(func.count(SessionItem.id)).where(SessionItem.session_id == session_id)
        )
        return int(result.scalar() or 0)

    async def count_done_for_session(self, session_id: int) -> int:
        result = await self.db.execute(
            select(func.count(SessionItem.id)).where(
                SessionItem.session_id == session_id,
                SessionItem.is_done == True,  # noqa: E712
            )
        )
        return int(result.scalar() or 0)

    async def count_discovery_for_user_on_date(
        self,
        user_id: int,
        session_date: date,
    ) -> int:
        result = await self.db.execute(
            select(func.count(SessionItem.id))
            .join(Session, Session.id == SessionItem.session_id)
            .where(
                Session.user_id == user_id,
                Session.session_date == session_date,
                SessionItem.source == SESSION_SOURCE_DISCOVERY,
            )
        )
        return int(result.scalar() or 0)

    async def count_correct_for_session(self, session_id: int) -> int:
        result = await self.db.execute(
            select(func.count(SessionItem.id)).where(
                SessionItem.session_id == session_id,
                SessionItem.is_done == True,  # noqa: E712
                SessionItem.is_correct == True,  # noqa: E712
            )
        )
        return int(result.scalar() or 0)

    async def list_answered_dates_for_user(self, user_id: int) -> list[date]:
        """Distinct calendar days with at least one answered session card."""
        result = await self.db.execute(
            select(func.date(SessionItem.answered_at))
            .join(Session, Session.id == SessionItem.session_id)
            .where(
                Session.user_id == user_id,
                SessionItem.is_done == True,  # noqa: E712
                SessionItem.answered_at.isnot(None),
            )
            .distinct()
        )
        return [row[0] for row in result.all() if row[0] is not None]

    async def count_answered_for_user_between(
        self,
        user_id: int,
        start: datetime,
        end: datetime,
    ) -> int:
        """Count done session cards answered in ``[start, end)``."""
        result = await self.db.execute(
            select(func.count(SessionItem.id))
            .join(Session, Session.id == SessionItem.session_id)
            .where(
                Session.user_id == user_id,
                SessionItem.is_done == True,  # noqa: E712
                SessionItem.answered_at.isnot(None),
                SessionItem.answered_at >= start,
                SessionItem.answered_at < end,
            )
        )
        return int(result.scalar() or 0)
