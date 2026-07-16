"""add battle and social tables

Revision ID: d4e5f6a7b8c9
Revises: c8d9e0f1a2b3
Create Date: 2026-05-15 18:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "d4e5f6a7b8c9"
down_revision = "c8d9e0f1a2b3"
branch_labels = None
depends_on = None

battle_mode = postgresql.ENUM(
    "quick",
    "ranked",
    "unranked",
    "typing",
    "voice",
    "ai",
    name="battlemode",
    create_type=False,
)
battle_status = postgresql.ENUM(
    "active",
    "finished",
    "cancelled",
    name="battlestatus",
    create_type=False,
)
battle_league = postgresql.ENUM(
    "bronze",
    "silver",
    "gold",
    "platinum",
    "diamond",
    name="battleleague",
    create_type=False,
)
friendship_status = postgresql.ENUM(
    "pending",
    "accepted",
    "blocked",
    name="friendshipstatus",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    sa.Enum(
        "quick",
        "ranked",
        "unranked",
        "typing",
        "voice",
        "ai",
        name="battlemode",
    ).create(bind, checkfirst=True)
    sa.Enum("active", "finished", "cancelled", name="battlestatus").create(
        bind, checkfirst=True
    )
    sa.Enum(
        "bronze",
        "silver",
        "gold",
        "platinum",
        "diamond",
        name="battleleague",
    ).create(bind, checkfirst=True)
    sa.Enum("pending", "accepted", "blocked", name="friendshipstatus").create(
        bind, checkfirst=True
    )

    op.create_table(
        "user_battle_stats",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("rating", sa.Integer(), server_default="1000", nullable=False),
        sa.Column("xp", sa.Integer(), server_default="0", nullable=False),
        sa.Column("wins", sa.Integer(), server_default="0", nullable=False),
        sa.Column("losses", sa.Integer(), server_default="0", nullable=False),
        sa.Column("draws", sa.Integer(), server_default="0", nullable=False),
        sa.Column("win_streak", sa.Integer(), server_default="0", nullable=False),
        sa.Column("best_win_streak", sa.Integer(), server_default="0", nullable=False),
        sa.Column("battles_played", sa.Integer(), server_default="0", nullable=False),
        sa.Column("league", battle_league, server_default="bronze", nullable=False),
        sa.Column("weekly_xp", sa.Integer(), server_default="0", nullable=False),
        sa.Column("season_week", sa.String(length=16), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_user_battle_stats_user_id", "user_battle_stats", ["user_id"])

    op.create_table(
        "battles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("mode", battle_mode, nullable=False),
        sa.Column("status", battle_status, server_default="active", nullable=False),
        sa.Column("is_ranked", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("round_count", sa.Integer(), server_default="3", nullable=False),
        sa.Column("round_seconds", sa.Integer(), server_default="15", nullable=False),
        sa.Column("season_week", sa.String(length=16), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_battles_season_week", "battles", ["season_week"])

    op.create_table(
        "battle_participants",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("battle_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("slot", sa.Integer(), nullable=False),
        sa.Column("display_name", sa.String(length=64), nullable=False),
        sa.Column("is_bot", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("rating_before", sa.Integer(), nullable=True),
        sa.Column("rating_after", sa.Integer(), nullable=True),
        sa.Column("score", sa.Integer(), server_default="0", nullable=False),
        sa.Column("xp_earned", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_winner", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(["battle_id"], ["battles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("battle_id", "slot", name="uq_battle_participant_slot"),
    )
    op.create_index("ix_battle_participants_battle_id", "battle_participants", ["battle_id"])
    op.create_index("ix_battle_participants_user_id", "battle_participants", ["user_id"])

    op.create_table(
        "battle_rounds",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("battle_id", sa.Integer(), nullable=False),
        sa.Column("round_index", sa.Integer(), nullable=False),
        sa.Column("prompt_text", sa.Text(), nullable=False),
        sa.Column("correct_answer", sa.String(length=255), nullable=False),
        sa.Column("player_answer", sa.String(length=255), nullable=True),
        sa.Column("player_correct", sa.Boolean(), nullable=True),
        sa.Column("player_time_ms", sa.Integer(), nullable=True),
        sa.Column("opponent_answer", sa.String(length=255), nullable=True),
        sa.Column("opponent_correct", sa.Boolean(), nullable=True),
        sa.Column("opponent_time_ms", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["battle_id"], ["battles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("battle_id", "round_index", name="uq_battle_round_index"),
    )
    op.create_index("ix_battle_rounds_battle_id", "battle_rounds", ["battle_id"])

    op.create_table(
        "friendships",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("requester_id", sa.Integer(), nullable=False),
        sa.Column("addressee_id", sa.Integer(), nullable=False),
        sa.Column("status", friendship_status, server_default="pending", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("accepted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["addressee_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requester_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("requester_id", "addressee_id", name="uq_friendship_pair"),
    )
    op.create_index("ix_friendships_requester_id", "friendships", ["requester_id"])
    op.create_index("ix_friendships_addressee_id", "friendships", ["addressee_id"])

    op.create_table(
        "friend_invite_codes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=12), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_friend_invite_codes_user_id", "friend_invite_codes", ["user_id"])
    op.create_index("ix_friend_invite_codes_code", "friend_invite_codes", ["code"])


def downgrade() -> None:
    op.drop_table("friend_invite_codes")
    op.drop_table("friendships")
    op.drop_table("battle_rounds")
    op.drop_table("battle_participants")
    op.drop_table("battles")
    op.drop_table("user_battle_stats")
    bind = op.get_bind()
    sa.Enum(name="friendshipstatus").drop(bind, checkfirst=True)
    sa.Enum(name="battleleague").drop(bind, checkfirst=True)
    sa.Enum(name="battlestatus").drop(bind, checkfirst=True)
    sa.Enum(name="battlemode").drop(bind, checkfirst=True)
