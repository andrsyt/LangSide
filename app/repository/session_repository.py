from datetime import date

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import Session, SessionStatus


class SessionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id_for_user(self, session_id: int, user_id: int) -> Session | None:
        result = await self.db.execute(
            select(Session).where(Session.id == session_id, Session.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user_and_date(self, user_id: int, session_date: date) -> Session | None:
        result = await self.db.execute(
            select(Session).where(
                Session.user_id == user_id,
                Session.session_date == session_date,
            )
        )
        return result.scalar_one_or_none()

    async def create_active(
        self,
        user_id: int,
        session_date: date,
        goal: int,
    ) -> Session:
        session = Session(
            user_id=user_id,
            session_date=session_date,
            goal=goal,
            status=SessionStatus.ACTIVE,
        )
        self.db.add(session)
        await self.db.flush()
        return session

    async def list_finished_dates_for_user(self, user_id: int) -> list[date]:
        result = await self.db.execute(
            select(Session.session_date)
            .where(
                Session.user_id == user_id,
                Session.status == SessionStatus.FINISHED,
            )
            .order_by(Session.session_date.asc())
        )
        return [row[0] for row in result.all()]

    async def delete_active_for_user(self, user_id: int) -> int:
        """Delete active today-sessions for the user. Returns deleted row count."""
        result = await self.db.execute(
            delete(Session).where(
                Session.user_id == user_id,
                Session.status == SessionStatus.ACTIVE,
            )
        )
        return int(result.rowcount or 0)
