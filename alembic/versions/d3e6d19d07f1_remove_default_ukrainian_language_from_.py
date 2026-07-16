"""Remove default ukrainian language from preferred_language

Revision ID: d3e6d19d07f1
Revises: 5f8158ff3f08
Create Date: 2026-01-27 15:51:13.471587

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd3e6d19d07f1'
down_revision = '5f8158ff3f08'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Змінюємо дефолтне значення колонки preferred_language з 'ukrainian' на NULL
    op.execute("ALTER TABLE users ALTER COLUMN preferred_language DROP DEFAULT")
    # Встановлюємо NULL як дефолтне значення (хоча це не обов'язково, але для ясності)
    op.execute("ALTER TABLE users ALTER COLUMN preferred_language SET DEFAULT NULL")


def downgrade() -> None:
    # Повертаємо дефолтне значення 'ukrainian'
    op.execute("ALTER TABLE users ALTER COLUMN preferred_language SET DEFAULT 'ukrainian'")

