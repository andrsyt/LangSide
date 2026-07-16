"""Celery tasks wrapping word + billing + AI services (full analyze pipeline)."""

from __future__ import annotations

from app.core.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.helpers.word_helpers import UserLanguageResolver
from app.repository.cache_repository import CacheRepository
from app.schemas.word import WordResponse
from app.services.words.ai_service import AIAnalysisService
from app.services.billing.billing_service import BillingService
from app.services.cache_service import cache_service
from app.services.words.word_service import WordAIAnalysisService, WordQueryService
from app.tasks.async_runner import run_async


async def _analyze_user_word_async(user_id: int, word_id: int) -> dict:
    async with AsyncSessionLocal() as session:
        queries = WordQueryService(session, user_id)
        word = await queries.get_word_by_id(word_id)
        billing = BillingService(session, user_id)

        if not await billing.check_rate_limits():
            return {"ok": False, "error": "rate_limit", "message": "Rate limit exceeded"}

        language_resolver = UserLanguageResolver(session, user_id)
        user_language = await language_resolver.get_user_target_language()

        ai = AIAnalysisService(session)
        analysis = await ai.analyze_word(
            word=word.word_text,
            difficulty_level=None,
            target_language=user_language,
        )

        word_ai = WordAIAnalysisService(session, user_id)
        updated = await word_ai.update_word_with_ai_analysis(word_id, analysis)
        await billing.record_api_usage()

        payload = WordResponse.model_validate(updated).model_dump()
        key = CacheRepository.user_word_snapshot_key(user_id, word_id)
        cache_service.set_json(key, payload)

        return {"ok": True, "word": payload}


@celery_app.task(name="words.analyze_user_word")
def analyze_user_word_task(user_id: int, word_id: int) -> dict:
    """
    Same pipeline as ``POST /words/{word_id}/analyze``: billing, AI, persist, usage, Redis snapshot.
    """
    return run_async(_analyze_user_word_async(user_id, word_id))
