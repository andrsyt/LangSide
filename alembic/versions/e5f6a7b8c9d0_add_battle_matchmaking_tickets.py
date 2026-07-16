"""add battle matchmaking tickets

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-05-16 10:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "e5f6a7b8c9d0"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None

matchmaking_status = postgresql.ENUM(
    "searching",
    "matched",
    "cancelled",
    "ai_started",
    name="matchmakingstatus",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    sa.Enum(
        "searching",
        "matched",
        "cancelled",
        "ai_started",
        name="matchmakingstatus",
    ).create(bind, checkfirst=True)

    op.create_table(
        "battle_matchmaking_tickets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("mode", sa.String(length=32), nullable=False),
        sa.Column("rating", sa.Integer(), server_default="1000", nullable=False),
        sa.Column("status", matchmaking_status, server_default="searching", nullable=False),
        sa.Column("opponent_user_id", sa.Integer(), nullable=True),
        sa.Column("battle_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("matched_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["battle_id"], ["battles.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["opponent_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_battle_matchmaking_tickets_user_id",
        "battle_matchmaking_tickets",
        ["user_id"],
    )
    op.create_index(
        "ix_battle_matchmaking_tickets_mode",
        "battle_matchmaking_tickets",
        ["mode"],
    )
    op.create_index(
        "ix_battle_matchmaking_tickets_status",
        "battle_matchmaking_tickets",
        ["status"],
    )


def downgrade() -> None:
    op.drop_table("battle_matchmaking_tickets")
    sa.Enum(name="matchmakingstatus").drop(op.get_bind(), checkfirst=True)
