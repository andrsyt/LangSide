"""add user public_id and allocator counter

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-05-19

"""

from alembic import op
import sqlalchemy as sa

PUBLIC_ID_INITIAL = 1_000_000

revision = "a7b8c9d0e1f2"
down_revision = "f6a7b8c9d0e1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("public_id", sa.BigInteger(), nullable=True),
    )

    # Первый пользователь — 1_000_000, далее +1 по порядку id
    op.execute(
        """
        WITH numbered AS (
            SELECT id, (ROW_NUMBER() OVER (ORDER BY id) + 999999)::bigint AS new_pid
            FROM users
        )
        UPDATE users AS u
        SET public_id = n.new_pid
        FROM numbered AS n
        WHERE u.id = n.id
        """
    )

    op.create_table(
        "user_public_id_counter",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("next_public_id", sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute(
        f"""
        INSERT INTO user_public_id_counter (id, next_public_id)
        SELECT 1, GREATEST(
            COALESCE((SELECT MAX(public_id) FROM users), {PUBLIC_ID_INITIAL - 1}) + 1,
            {PUBLIC_ID_INITIAL}
        )
        """
    )

    op.alter_column("users", "public_id", nullable=False)
    op.create_index("ix_users_public_id", "users", ["public_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_public_id", table_name="users")
    op.drop_column("users", "public_id")
    op.drop_table("user_public_id_counter")
