"""reduce study status to learning/mastered

Revision ID: 9f2a1c7d4b10
Revises: 1b7555c83d3d
Create Date: 2026-03-21 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9f2a1c7d4b10"
down_revision = "1b7555c83d3d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Normalize existing values first.
    op.execute(
        """
        UPDATE words
        SET study_status = 'learning'
        WHERE study_status IS NULL OR study_status IN ('new', 'reviewing')
        """
    )

    # Recreate enum with only two allowed values.
    op.execute("ALTER TYPE studystatus RENAME TO studystatus_old")
    op.execute("CREATE TYPE studystatus AS ENUM ('learning', 'mastered')")
    op.execute(
        """
        ALTER TABLE words
        ALTER COLUMN study_status TYPE studystatus
        USING study_status::text::studystatus
        """
    )
    op.execute("ALTER TABLE words ALTER COLUMN study_status SET DEFAULT 'learning'")
    op.execute("DROP TYPE studystatus_old")


def downgrade() -> None:
    op.execute("ALTER TYPE studystatus RENAME TO studystatus_old")
    op.execute("CREATE TYPE studystatus AS ENUM ('new', 'learning', 'reviewing', 'mastered')")
    op.execute(
        """
        ALTER TABLE words
        ALTER COLUMN study_status TYPE studystatus
        USING study_status::text::studystatus
        """
    )
    op.execute("ALTER TABLE words ALTER COLUMN study_status SET DEFAULT 'new'")
    op.execute("DROP TYPE studystatus_old")
