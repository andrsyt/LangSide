"""double_recall_sessions: current_step, synonyms_submitted

Revision ID: e8f1a2b3c4d5
Revises: 2b9404d5b40f
Create Date: 2026-05-09

"""
from alembic import op
import sqlalchemy as sa


revision = "e8f1a2b3c4d5"
down_revision = "2b9404d5b40f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "double_recall_sessions",
        sa.Column("current_step", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "double_recall_sessions",
        sa.Column("synonyms_submitted", sa.JSON(), nullable=True),
    )
    op.alter_column(
        "double_recall_sessions",
        "current_step",
        server_default=None,
        existing_type=sa.Integer(),
    )


def downgrade() -> None:
    op.drop_column("double_recall_sessions", "synonyms_submitted")
    op.drop_column("double_recall_sessions", "current_step")
