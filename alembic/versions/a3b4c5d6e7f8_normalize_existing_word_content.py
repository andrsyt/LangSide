"""Normalize existing word content (translation / explanation / examples).

One-time data migration: applies the same normalization rules used on write
(see app/helpers/text_utils.py) to rows that were saved before normalization
existed. Irreversible — original raw values are not preserved.

Revision ID: a3b4c5d6e7f8
Revises: f2a3b4c5d6e7
"""

from alembic import op
import sqlalchemy as sa

from app.helpers.text_utils import normalize_sentence, normalize_translation

revision = "a3b4c5d6e7f8"
down_revision = "f2a3b4c5d6e7"
branch_labels = None
depends_on = None


def _normalize_examples(raw: str) -> str | None:
    """Examples are stored newline-joined; normalize each line as a sentence."""
    normalized = [normalize_sentence(line, max_words=15) for line in raw.split("\n")]
    normalized = [line for line in normalized if line]
    return "\n".join(normalized) or None


def upgrade() -> None:
    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            "SELECT id, translation, explanation, examples FROM words "
            "WHERE translation IS NOT NULL "
            "OR explanation IS NOT NULL "
            "OR examples IS NOT NULL"
        )
    ).fetchall()

    update_stmt = sa.text(
        "UPDATE words SET "
        "translation = :translation, "
        "explanation = :explanation, "
        "examples = :examples "
        "WHERE id = :id"
    )

    for row in rows:
        new_translation = row.translation
        if row.translation is not None:
            new_translation = normalize_translation(row.translation) or None

        new_explanation = row.explanation
        if row.explanation is not None:
            new_explanation = normalize_sentence(row.explanation) or None

        new_examples = row.examples
        if row.examples is not None:
            new_examples = _normalize_examples(row.examples)

        unchanged = (
            new_translation == row.translation
            and new_explanation == row.explanation
            and new_examples == row.examples
        )
        if unchanged:
            continue

        conn.execute(
            update_stmt,
            {
                "id": row.id,
                "translation": new_translation,
                "explanation": new_explanation,
                "examples": new_examples,
            },
        )


def downgrade() -> None:
    # Irreversible: original (pre-normalization) values are not stored.
    pass
