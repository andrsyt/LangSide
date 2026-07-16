from __future__ import annotations

from sqlalchemy import BigInteger, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.core.public_user_id import PUBLIC_ID_INITIAL
from app.db.base import Base


class UserPublicIdCounter(Base):
    """
    Singleton counter for atomic public_id allocation (SELECT … FOR UPDATE).
    Single row: id=1.
    """

    __tablename__ = "user_public_id_counter"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    next_public_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=PUBLIC_ID_INITIAL,
    )
