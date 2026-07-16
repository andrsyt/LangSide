"""Add quests table

Revision ID: add_quests_table_001
Revises: d3e6d19d07f1
Create Date: 2026-01-31 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'add_quests_table_001'
down_revision = 'd3e6d19d07f1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Створюємо enum для QuestType (якщо ще не існує)
    conn = op.get_bind()
    # Перевіряємо, чи існує тип
    result = conn.execute(
        text("SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'questtype')")
    ).scalar()
    
    questtype_enum = postgresql.ENUM(
        'multiple_choice',
        'fill_in_the_blank',
        'matching',
        'true_false',
        'ordering',
        'classification',
        'rearrangement',
        'short_answer',
        'essay',
        'problem_solving',
        'research',
        name='questtype',
        create_type=False  # Не створюємо тип, якщо він вже існує
    )
    
    if not result:
        questtype_enum.create(conn, checkfirst=True)
    
    # Створюємо таблицю quests
    # Використовуємо існуючий тип difficultylevel (він вже створений в попередніх міграціях)
    difficulty_enum = postgresql.ENUM('A1', 'A2', 'B1', 'B2', 'C1', 'C2', name='difficultylevel', create_type=False)
    
    op.create_table('quests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('word_id', sa.Integer(), nullable=False),
        sa.Column('quest_type', questtype_enum, nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('correct_answer', sa.Text(), nullable=False),
        sa.Column('options', sa.JSON(), nullable=False),
        sa.Column('difficulty', difficulty_enum, nullable=False),
        sa.Column('is_completed', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('is_correct', sa.Boolean(), nullable=True),
        sa.Column('user_answer', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('answered_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['word_id'], ['words.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Створюємо індекси
    op.create_index(op.f('ix_quests_user_id'), 'quests', ['user_id'], unique=False)
    op.create_index(op.f('ix_quests_word_id'), 'quests', ['word_id'], unique=False)
    op.create_index(op.f('ix_quests_is_completed'), 'quests', ['is_completed'], unique=False)
    op.create_index(op.f('ix_quests_created_at'), 'quests', ['created_at'], unique=False)


def downgrade() -> None:
    # Видаляємо індекси
    op.drop_index(op.f('ix_quests_created_at'), table_name='quests')
    op.drop_index(op.f('ix_quests_is_completed'), table_name='quests')
    op.drop_index(op.f('ix_quests_word_id'), table_name='quests')
    op.drop_index(op.f('ix_quests_user_id'), table_name='quests')
    
    # Видаляємо таблицю
    op.drop_table('quests')
    
    # Видаляємо enum
    questtype_enum = postgresql.ENUM(
        'multiple_choice',
        'fill_in_the_blank',
        'matching',
        'true_false',
        'ordering',
        'classification',
        'rearrangement',
        'short_answer',
        'essay',
        'problem_solving',
        'research',
        name='questtype'
    )
    questtype_enum.drop(op.get_bind(), checkfirst=True)

