"""add_common_word_table

Revision ID: 6c1895695e67
Revises: add_quests_table_001
Create Date: 2026-02-02 18:48:05.837335

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '6c1895695e67'
down_revision = 'add_quests_table_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Використовуємо існуючий enum типу (create_type=False)
    difficulty_enum = postgresql.ENUM('A1', 'A2', 'B1', 'B2', 'C1', 'C2', name='difficultylevel', create_type=False)
    
    # Створюємо таблицю common_words
    op.create_table(
        'common_words',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('word_text', sa.String(length=255), nullable=False),
        sa.Column('cefr_level', difficulty_enum, nullable=False),
        sa.Column('is_everyday_common', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('word_text')
    )
    
    # Створюємо індекси для швидкого пошуку
    op.create_index(op.f('ix_common_words_word_text'), 'common_words', ['word_text'], unique=True)
    op.create_index('ix_common_words_cefr_level', 'common_words', ['cefr_level'], unique=False)
    op.create_index('ix_common_words_is_everyday_common', 'common_words', ['is_everyday_common'], unique=False)


def downgrade() -> None:
    # Видаляємо індекси
    op.drop_index('ix_common_words_is_everyday_common', table_name='common_words')
    op.drop_index('ix_common_words_cefr_level', table_name='common_words')
    op.drop_index(op.f('ix_common_words_word_text'), table_name='common_words')
    
    # Видаляємо таблицю
    op.drop_table('common_words')

