"""Migration: preferred_language enum -> VARCHAR canonical codes."""

from alembic import op
import sqlalchemy as sa

revision = "b4c5d6e7f8a9"
down_revision = "a3b4c5d6e7f8"
branch_labels = None
depends_on = None

_LEGACY_TO_CANONICAL = {
    "ukrainian": "uk",
    "russian": "ru",
    "polish": "pl",
    "german": "de",
    "french": "fr",
    "spanish": "es",
    "italian": "it",
    "english": "en",
}


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("preferred_language_code", sa.String(length=16), nullable=True),
    )

    case_lines = [
        f"WHEN preferred_language::text = '{legacy}' THEN '{canonical}'"
        for legacy, canonical in _LEGACY_TO_CANONICAL.items()
    ]
    case_sql = "\n                ".join(case_lines)
    op.execute(
        f"""
        UPDATE users
        SET preferred_language_code = CASE
                {case_sql}
                ELSE NULL
            END
        WHERE preferred_language IS NOT NULL
        """
    )

    op.drop_column("users", "preferred_language")
    op.alter_column(
        "users",
        "preferred_language_code",
        new_column_name="preferred_language",
        existing_type=sa.String(length=16),
        existing_nullable=True,
    )
    op.execute("DROP TYPE IF EXISTS language")


def downgrade() -> None:
    language_enum = sa.Enum(
        "ukrainian",
        "english",
        "russian",
        "polish",
        "german",
        "french",
        "spanish",
        "italian",
        name="language",
    )
    language_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "users",
        sa.Column(
            "preferred_language_enum",
            language_enum,
            nullable=True,
        ),
    )

    canonical_to_legacy = {v: k for k, v in _LEGACY_TO_CANONICAL.items()}
    case_lines = [
        f"WHEN preferred_language = '{canonical}' THEN '{legacy}'"
        for canonical, legacy in canonical_to_legacy.items()
    ]
    case_sql = "\n                ".join(case_lines)
    op.execute(
        f"""
        UPDATE users
        SET preferred_language_enum = CASE
                {case_sql}
                ELSE NULL
            END::language
        WHERE preferred_language IS NOT NULL
        """
    )

    op.drop_column("users", "preferred_language")
    op.alter_column(
        "users",
        "preferred_language_enum",
        new_column_name="preferred_language",
        existing_type=language_enum,
        existing_nullable=True,
    )
