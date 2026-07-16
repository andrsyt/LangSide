"""learning sessions, semantic anchor sessions, normalized training storage

Revision ID: f1e2d3c4b5a6
Revises: e8f1a2b3c4d5
Create Date: 2026-05-11 15:45:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "f1e2d3c4b5a6"
down_revision = "e8f1a2b3c4d5"
branch_labels = None
depends_on = None


learning_session_status = postgresql.ENUM(
    "active",
    "finished",
    name="learningsessionstatus",
    create_type=False,
)
learning_quest_type = postgresql.ENUM(
    "semantic_anchor",
    "double_recall",
    "anti_confusion",
    "association_recall",
    name="learningquesttype",
    create_type=False,
)


def upgrade() -> None:
    op.add_column("trainings", sa.Column("semantic_anchor_data", sa.JSON(), nullable=True))
    op.add_column("trainings", sa.Column("freeform_associations", sa.JSON(), nullable=True))
    op.add_column("trainings", sa.Column("association_v2_data", sa.JSON(), nullable=True))
    op.add_column("trainings", sa.Column("association_recall_cue", sa.String(), nullable=True))
    op.add_column("trainings", sa.Column("completed_quest_types", sa.JSON(), nullable=True))

    op.add_column("word_cards", sa.Column("semantic_anchor_data", sa.JSON(), nullable=True))
    op.add_column("word_cards", sa.Column("association_v2_data", sa.JSON(), nullable=True))

    op.create_table(
        "semantic_anchor_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("word_id", sa.Integer(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("example", sa.Text(), nullable=False),
        sa.Column("anchor_variants", sa.JSON(), nullable=False),
        sa.Column("context_variants", sa.JSON(), nullable=False),
        sa.Column("correct_context_index", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["word_id"], ["words.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_semantic_anchor_sessions_user_id"),
        "semantic_anchor_sessions",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_semantic_anchor_sessions_word_id"),
        "semantic_anchor_sessions",
        ["word_id"],
        unique=False,
    )

    learning_session_status.create(op.get_bind(), checkfirst=True)
    learning_quest_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "learning_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("session_date", sa.Date(), nullable=False),
        sa.Column("goal", sa.Integer(), nullable=False),
        sa.Column("status", learning_session_status, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_learning_sessions_user_id"), "learning_sessions", ["user_id"], unique=False)
    op.create_index(op.f("ix_learning_sessions_session_date"), "learning_sessions", ["session_date"], unique=False)

    op.create_table(
        "learning_session_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("learning_session_id", sa.Integer(), nullable=False),
        sa.Column("word_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("quest_type", learning_quest_type, nullable=False),
        sa.Column("source_bucket", sa.String(), nullable=True),
        sa.Column("is_done", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_correct", sa.Boolean(), nullable=True),
        sa.Column("result_payload", sa.JSON(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["learning_session_id"], ["learning_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["word_id"], ["words.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_learning_session_items_learning_session_id"),
        "learning_session_items",
        ["learning_session_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_learning_session_items_word_id"),
        "learning_session_items",
        ["word_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_learning_session_items_word_id"), table_name="learning_session_items")
    op.drop_index(op.f("ix_learning_session_items_learning_session_id"), table_name="learning_session_items")
    op.drop_table("learning_session_items")

    op.drop_index(op.f("ix_learning_sessions_session_date"), table_name="learning_sessions")
    op.drop_index(op.f("ix_learning_sessions_user_id"), table_name="learning_sessions")
    op.drop_table("learning_sessions")

    learning_quest_type.drop(op.get_bind(), checkfirst=True)
    learning_session_status.drop(op.get_bind(), checkfirst=True)

    op.drop_index(op.f("ix_semantic_anchor_sessions_word_id"), table_name="semantic_anchor_sessions")
    op.drop_index(op.f("ix_semantic_anchor_sessions_user_id"), table_name="semantic_anchor_sessions")
    op.drop_table("semantic_anchor_sessions")

    op.drop_column("word_cards", "association_v2_data")
    op.drop_column("word_cards", "semantic_anchor_data")

    op.drop_column("trainings", "completed_quest_types")
    op.drop_column("trainings", "association_recall_cue")
    op.drop_column("trainings", "association_v2_data")
    op.drop_column("trainings", "freeform_associations")
    op.drop_column("trainings", "semantic_anchor_data")
