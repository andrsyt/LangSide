"""double recall gloss recall, example and own sentence flags

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
Create Date: 2026-05-19

"""

from alembic import op
import sqlalchemy as sa

revision = "c9d0e1f2a3b4"
down_revision = "b8c9d0e1f2a3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "double_recall_sessions",
        sa.Column(
            "gloss_recall_passed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "double_recall_sessions",
        sa.Column("example_passed", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "double_recall_sessions",
        sa.Column("own_sentence_passed", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "double_recall_sessions",
        sa.Column("own_sentence_text", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("double_recall_sessions", "own_sentence_text")
    op.drop_column("double_recall_sessions", "own_sentence_passed")
    op.drop_column("double_recall_sessions", "example_passed")
    op.drop_column("double_recall_sessions", "gloss_recall_passed")
