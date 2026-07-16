"""add user_daily_activity table

Revision ID: c8d9e0f1a2b3
Revises: f1e2d3c4b5a6
Create Date: 2026-05-15 12:00:00

"""
from alembic import op
import sqlalchemy as sa


revision = "c8d9e0f1a2b3"
down_revision = "f1e2d3c4b5a6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_daily_activity",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("activity_date", sa.Date(), nullable=False),
        sa.Column("exercises_completed", sa.Integer(), server_default="0", nullable=False),
        sa.Column("words_reviewed", sa.Integer(), server_default="0", nullable=False),
        sa.Column("words_added", sa.Integer(), server_default="0", nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "activity_date",
            name="uq_user_daily_activity_user_date",
        ),
    )
    op.create_index(
        op.f("ix_user_daily_activity_user_id"),
        "user_daily_activity",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_user_daily_activity_activity_date"),
        "user_daily_activity",
        ["activity_date"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_user_daily_activity_activity_date"),
        table_name="user_daily_activity",
    )
    op.drop_index(
        op.f("ix_user_daily_activity_user_id"),
        table_name="user_daily_activity",
    )
    op.drop_table("user_daily_activity")
