import json
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.core.language_codes import default_language_code
from app.core.config import settings
from app.helpers.ai_analysis_helper import (
    AIAnalysisCacheHelper,
    GroqWordAnalysisHelper,
)
from app.helpers.translation_helper import translate_word
from app.helpers.ai_analysis_helper import VocabularyLookupHelper
from app.schemas.ai import WordAnalysisResponse
from app.models.word import DifficultyLevel
from app.services.cache_service import get_cache, set_cache

logger = logging.getLogger(__name__)

class AIAnalysisService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.vocabulary = VocabularyLookupHelper(db)
        self.groq = GroqWordAnalysisHelper()

    async def analyze_word(
        self,
        word: str,
        difficulty_level: Optional[DifficultyLevel] = None,
        target_language: str | None = None,
    ) -> WordAnalysisResponse:
        language = target_language or default_language_code()
        translation = await translate_word(word, language)
        word_level_from_db = await self.vocabulary.get_word_level(word)
        cache_key = AIAnalysisCacheHelper.build_cache_key(word, language)
        cached_result = get_cache(cache_key)

        if not translation:
            logger.warning(f"Failed to translate word '{word}' to {language}")
        
        if word_level_from_db:
            difficulty_level = word_level_from_db
            logger.info(f"Word '{word}' found in common words DB with level: {difficulty_level}")

        if cached_result:
            cached_analysis = AIAnalysisCacheHelper.process_cached_data(
                cached_result,
                word_level_from_db,
            )
            if cached_analysis:
                return cached_analysis

        if settings.AI_PROVIDER == "groq":
            analysis_data = await self.groq.analyze_word(
                word=word,
                difficulty_level=difficulty_level,
                translation=translation or "",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unsupported or disabled AI provider: {settings.AI_PROVIDER}"
            )

        set_cache(cache_key, json.dumps(analysis_data.model_dump()))
        return analysis_data