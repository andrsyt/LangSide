"""add anti_confusion_session table

Revision ID: f7e8d9c0b1a2
Revises: c4a647cd827b
Create Date: 2026-05-04

"""
from alembic import op
import sqlalchemy as sa


revision = "f7e8d9c0b1a2"
down_revision = "c4a647cd827b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "anti_confusion_session",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("word_id", sa.Integer(), nullable=False),
        sa.Column("options", sa.JSON(), nullable=False),
        sa.Column("correct_index", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["word_id"], ["words.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_anti_confusion_session_user_id"),
        "anti_confusion_session",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_anti_confusion_session_word_id"),
        "anti_confusion_session",
        ["word_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_anti_confusion_session_word_id"), table_name="anti_confusion_session")
    op.drop_index(op.f("ix_anti_confusion_session_user_id"), table_name="anti_confusion_session")
    op.drop_table("anti_confusion_session")
