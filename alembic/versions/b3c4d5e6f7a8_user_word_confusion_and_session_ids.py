"""user_word_confusion table; option_word_ids; example_neighbor_word_ids

Revision ID: b3c4d5e6f7a8
Revises: a9b8c7d6e5f4
Create Date: 2026-05-11

"""
from alembic import op
import sqlalchemy as sa


revision = "b3c4d5e6f7a8"
down_revision = "a9b8c7d6e5f4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_word_confusion",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("word_id", sa.Integer(), nullable=False),
        sa.Column("neighbor_word_id", sa.Integer(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["neighbor_word_id"], ["words.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["word_id"], ["words.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "word_id", "neighbor_word_id", name="uq_user_word_confusion_pair"),
    )
    op.create_index(op.f("ix_user_word_confusion_user_id"), "user_word_confusion", ["user_id"], unique=False)
    op.create_index(op.f("ix_user_word_confusion_word_id"), "user_word_confusion", ["word_id"], unique=False)
    op.create_index(op.f("ix_user_word_confusion_neighbor_word_id"), "user_word_confusion", ["neighbor_word_id"], unique=False)

    op.add_column(
        "anti_confusion_session",
        sa.Column("option_word_ids", sa.JSON(), nullable=True),
    )
    op.add_column(
        "double_recall_sessions",
        sa.Column("example_neighbor_word_ids", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("double_recall_sessions", "example_neighbor_word_ids")
    op.drop_column("anti_confusion_session", "option_word_ids")
    op.drop_index(op.f("ix_user_word_confusion_neighbor_word_id"), table_name="user_word_confusion")
    op.drop_index(op.f("ix_user_word_confusion_word_id"), table_name="user_word_confusion")
    op.drop_index(op.f("ix_user_word_confusion_user_id"), table_name="user_word_confusion")
    op.drop_table("user_word_confusion")
