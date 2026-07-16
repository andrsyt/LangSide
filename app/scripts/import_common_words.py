import asyncio
import sys
from pathlib import Path

# Add project root to PYTHONPATH
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.helpers.english_words_csv import EnglishWords
from app.models.common_word import CommonWord
from app.models.word import DifficultyLevel

# Map level strings to DifficultyLevel enum
LEVEL_MAP = {
    "a1": DifficultyLevel.A1,
    "a2": DifficultyLevel.A2,
    "b1": DifficultyLevel.B1,
    "b2": DifficultyLevel.B2,
    "c1": DifficultyLevel.C1,
    "c2": DifficultyLevel.C2,
}

CEFR_ORDER = {
    DifficultyLevel.A1: 1,
    DifficultyLevel.A2: 2,
    DifficultyLevel.B1: 3,
    DifficultyLevel.B2: 4,
    DifficultyLevel.C1: 5,
    DifficultyLevel.C2: 6,
}


async def import_common_words(db: AsyncSession):
    """Import common words from a CSV file into the database."""
    csv_path = project_root / "localization" / "oxford-5000.csv"
    english_words = EnglishWords(str(csv_path))
    all_levels_words = english_words.get_all_levels_words()

    total_added = 0
    total_skipped = 0

    for level_str, words in all_levels_words.items():
        # Convert level string to enum
        if level_str.lower() not in LEVEL_MAP:
            print(f"Warning: Unknown level '{level_str}', skipping...")
            continue

        level_enum = LEVEL_MAP[level_str.lower()]
        level_added = 0

        for word in words:
            # Skip if the word already exists
            normalized_word = word.strip().lower()
            result = await db.execute(
                select(CommonWord).where(CommonWord.word_text == normalized_word)
            )
            existing_word = result.scalar_one_or_none()

            if existing_word is None:
                # Create a new word row
                db_word = CommonWord(
                    word_text=normalized_word,
                    cefr_level=level_enum,
                    is_everyday_common=True,
                )
                db.add(db_word)
                level_added += 1
                total_added += 1
            else:
                # If duplicates have different POS/levels, keep easier CEFR level.
                if CEFR_ORDER[level_enum] < CEFR_ORDER[existing_word.cefr_level]:
                    existing_word.cefr_level = level_enum
                total_skipped += 1

        # Commit after each level for better throughput
        await db.commit()
        print(
            f"Level {level_str.upper()}: Added {level_added} words, skipped {len(words) - level_added} duplicates"
        )

    print(
        f"\nImport completed: {total_added} words added, {total_skipped} duplicates skipped"
    )


async def main():
    """Entry point for running the import."""
    # Create engine and session
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as db:
        try:
            await import_common_words(db)
        except Exception as e:
            print(f"Error during import: {str(e)}")
            await db.rollback()
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
