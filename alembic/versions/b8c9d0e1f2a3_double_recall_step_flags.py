"""double recall translation_passed and synonyms_passed

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-05-19

"""

from alembic import op
import sqlalchemy as sa

revision = "b8c9d0e1f2a3"
down_revision = "a7b8c9d0e1f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "double_recall_sessions",
        sa.Column(
            "translation_passed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "double_recall_sessions",
        sa.Column("synonyms_passed", sa.Boolean(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("double_recall_sessions", "synonyms_passed")
    op.drop_column("double_recall_sessions", "translation_passed")
