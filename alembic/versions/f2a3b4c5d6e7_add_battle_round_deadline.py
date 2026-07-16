"""Add round_deadline_at to battles for server-side round timers.

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6
"""

from alembic import op
import sqlalchemy as sa

revision = "f2a3b4c5d6e7"
down_revision = "e1f2a3b4c5d6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "battles",
        sa.Column("round_deadline_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("battles", "round_deadline_at")
