"""add_test_sessions_table

Revision ID: add_test_sessions_001
Revises: 6c1895695e67
Create Date: 2026-02-02 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'add_test_sessions_001'
down_revision = '6c1895695e67'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Перевіряємо, чи існує тип testsessionstatus
    conn = op.get_bind()
    result = conn.execute(
        text("SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'testsessionstatus')")
    ).scalar()
    
    testsessionstatus_enum = postgresql.ENUM(
        'in_progress',
        'round1_completed',
        'round2_completed',
        'finished',
        name='testsessionstatus',
        create_type=False
    )
    
    if not result:
        testsessionstatus_enum.create(conn, checkfirst=True)
    
    # Використовуємо існуючий тип difficultylevel
    difficulty_enum = postgresql.ENUM('A1', 'A2', 'B1', 'B2', 'C1', 'C2', name='difficultylevel', create_type=False)
    
    # Створюємо таблицю test_sessions
    op.create_table(
        'test_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('difficulty', difficulty_enum, nullable=False),
        sa.Column('total_questions', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('round', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', testsessionstatus_enum, nullable=False, server_default='in_progress'),
        sa.Column('current_question_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('round1_correct_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('round1_incorrect_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('round2_correct_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('round2_incorrect_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('round1_completed_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Створюємо індекси
    op.create_index(op.f('ix_test_sessions_user_id'), 'test_sessions', ['user_id'], unique=False)
    
    # Додаємо поля до таблиці quests
    op.add_column('quests', sa.Column('test_session_id', sa.Integer(), nullable=True))
    op.add_column('quests', sa.Column('round', sa.Integer(), nullable=True))
    op.add_column('quests', sa.Column('question_index', sa.Integer(), nullable=True))
    op.add_column('quests', sa.Column('is_retry', sa.Boolean(), nullable=True, server_default='false'))
    
    # Створюємо foreign key для test_session_id
    op.create_foreign_key(
        'fk_quests_test_session_id',
        'quests',
        'test_sessions',
        ['test_session_id'],
        ['id'],
        ondelete='CASCADE'
    )
    
    # Створюємо індекси
    op.create_index(op.f('ix_quests_test_session_id'), 'quests', ['test_session_id'], unique=False)


def downgrade() -> None:
    # Видаляємо індекси
    op.drop_index(op.f('ix_quests_test_session_id'), table_name='quests')
    op.drop_index(op.f('ix_test_sessions_user_id'), table_name='test_sessions')
    
    # Видаляємо foreign key
    op.drop_constraint('fk_quests_test_session_id', 'quests', type_='foreignkey')
    
    # Видаляємо колонки з quests
    op.drop_column('quests', 'is_retry')
    op.drop_column('quests', 'question_index')
    op.drop_column('quests', 'round')
    op.drop_column('quests', 'test_session_id')
    
    # Видаляємо таблицю test_sessions
    op.drop_table('test_sessions')
    
    # Видаляємо enum (якщо він не використовується в інших таблицях)
    # Але краще залишити його для майбутнього використання

