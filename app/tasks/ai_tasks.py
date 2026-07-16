"""Celery tasks wrapping :class:`AIAnalysisService` (no user word persistence)."""

from __future__ import annotations

import logging

from app.core.celery_app import celery_app
from app.core.language_codes import default_language_code
from app.db.session import AsyncSessionLocal
from app.models.word import DifficultyLevel
from app.services.words.ai_service import AIAnalysisService
from app.tasks.async_runner import run_async

logger = logging.getLogger(__name__)


async def _analyze_word_async(
    word: str,
    target_language: str,
    difficulty_level: str | None,
) -> dict:
    async with AsyncSessionLocal() as session:
        svc = AIAnalysisService(session)
        level: DifficultyLevel | None = None
        if difficulty_level:
            level = DifficultyLevel(difficulty_level)
        result = await svc.analyze_word(
            word=word,
            difficulty_level=level,
            target_language=target_language,
        )
        return result.model_dump()


@celery_app.task(name="ai.analyze_word")
def analyze_word_task(
    word: str,
    target_language: str | None = None,
    difficulty_level: str | None = None,
) -> dict:
    """
    Async Groq/local analysis for a free-form English word (same logic as API ``AIAnalysisService``).
    """
    try:
        language = target_language or default_language_code()
        return run_async(_analyze_word_async(word, language, difficulty_level))
    except ValueError as exc:
        logger.warning("analyze_word_task: invalid difficulty %r: %s", difficulty_level, exc)
        raise
