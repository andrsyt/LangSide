"""add anonymous columns to users

Revision ID: c4a647cd827b
Revises: ef563545bd52
Create Date: 2026-04-10 19:54:51.112136

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c4a647cd827b'
down_revision = 'ef563545bd52'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("device_hash", sa.String(), nullable=True))
    op.add_column(
        "users",
        sa.Column(
            "is_anonymous",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.create_index("ix_users_device_hash", "users", ["device_hash"], unique=True)
    op.create_index("ix_users_is_anonymous", "users", ["is_anonymous"], unique=False)
    op.alter_column("users", "is_anonymous", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_users_is_anonymous", table_name="users")
    op.drop_index("ix_users_device_hash", table_name="users")
    op.drop_column("users", "is_anonymous")
    op.drop_column("users", "device_hash")

