"""add double_recall_sessions table

Revision ID: a9b8c7d6e5f4
Revises: f7e8d9c0b1a2
Create Date: 2026-05-10

"""
from alembic import op
import sqlalchemy as sa


revision = "a9b8c7d6e5f4"
down_revision = "f7e8d9c0b1a2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "double_recall_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("word_id", sa.Integer(), nullable=False),
        sa.Column("example_sentences", sa.JSON(), nullable=False),
        sa.Column("correct_example_index", sa.Integer(), nullable=False),
        sa.Column("min_synonyms", sa.Integer(), nullable=False),
        sa.Column("translation_prompt", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["word_id"], ["words.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_double_recall_sessions_user_id"),
        "double_recall_sessions",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_double_recall_sessions_word_id"),
        "double_recall_sessions",
        ["word_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_double_recall_sessions_word_id"), table_name="double_recall_sessions")
    op.drop_index(op.f("ix_double_recall_sessions_user_id"), table_name="double_recall_sessions")
    op.drop_table("double_recall_sessions")
