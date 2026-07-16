from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "d0e1f2a3b4c5"  # свой id
down_revision = "c9d0e1f2a3b4"      # твой heads

def upgrade():
    difficulty_enum = postgresql.ENUM(
        "A1", "A2", "B1", "B2", "C1", "C2",
        name="difficultylevel",
        create_type=False,  # тип УЖЕ есть в БД
    )
    op.add_column(
        "users",
        sa.Column(
            "english_level",
            difficulty_enum,
            nullable=False,
            server_default="B1",
        ),
    )

def downgrade():
    op.drop_column("users", "english_level")