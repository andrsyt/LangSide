"""Today session rotation and item source tracking.

Revision ID: e1f2a3b4c5d6
Revises: d0e1f2a3b4c5
"""

from alembic import op
import sqlalchemy as sa

revision = "e1f2a3b4c5d6"
down_revision = "d0e1f2a3b4c5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "words",
        sa.Column("last_today_session_at", sa.DateTime(), nullable=True),
    )
    op.create_index(
        "ix_words_user_last_today_session",
        "words",
        ["user_id", "last_today_session_at"],
    )
    op.add_column(
        "session_items",
        sa.Column("source", sa.String(length=32), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("session_items", "source")
    op.drop_index("ix_words_user_last_today_session", table_name="words")
    op.drop_column("words", "last_today_session_at")
