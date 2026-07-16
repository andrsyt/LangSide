from __future__ import annotations

import json
import logging
import re

import httpx
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.helpers.text_utils import (
    alphabetic_english_word_key,
    canonical_english_word_key,
    extract_fenced_llm_content,
    infer_cefr_value_string_from_ai,
)
from app.models.word import DifficultyLevel
from app.repository.common_word_repository import CommonWordRepository
from app.schemas.ai import WordAnalysisResponse

logger = logging.getLogger(__name__)


class AIAnalysisCacheHelper:
    """Handles cache-related helpers for AI word analysis."""

    @staticmethod
    def build_cache_key(word: str, target_language: str) -> str:
        return f"word_analysis:{canonical_english_word_key(word)}:{target_language}"

    @staticmethod
    def process_cached_data(
        cached_result: str,
        word_level_from_db: DifficultyLevel | None,
    ) -> WordAnalysisResponse | None:
        try:
            data = json.loads(cached_result)
            if word_level_from_db and data.get("difficulty") != word_level_from_db.value:
                data["difficulty"] = word_level_from_db.value
            return WordAnalysisResponse(**data)
        except (json.JSONDecodeError, ValueError):
            return None


class AIAnalysisPromptHelper:
    """Builds prompts for AI vocabulary analysis."""

    @staticmethod
    def build_prompt(word: str) -> str:
        cefr_guidelines = """
CEFR Level Guidelines:
- A1 (Beginner): Basic words (100-500 words). Simple, concrete objects.
- A2 (Elementary): Daily life (500-1500 words). Varied vocabulary.
- B1 (Intermediate): Opinions/Ideas (1500-3000 words). Abstract concepts.
- B2 (Upper-intermediate): Sophisticated (3000-5000 words). Complex texts.
- C1 (Advanced): Academic/Professional (5000-8000 words).
- C2 (Proficient): Rare/Idioms (8000+ words).
IMPORTANT: Prioritize everyday common words.
"""
        return f"""You are an English vocabulary assistant. For the English word "{word}" do the following.
{cefr_guidelines}
Your task: 1. SHORT explanation (1-2 sentences, <100 chars). 2. Exactly 3 SHORT example sentences (each <15 words). 3. Determine CEFR level (A1-C2).
Format as JSON: {{"explanation": "...", "examples": ["...", "...", "..."], "difficulty": "A1"}}"""


class AIAnalysisResponseHelper:
    """Normalizes AI analysis payloads into API-ready data."""

    @staticmethod
    def clean_analysis_data(analysis: dict) -> tuple[str, list[str]]:
        explanation = analysis.get("explanation", "").strip()
        if len(explanation) > 100:
            if "." in explanation[:100]:
                explanation = explanation[: explanation[:100].rfind(".") + 1].strip()
            else:
                explanation = explanation[:97] + "..."

        short_examples: list[str] = []
        for example in analysis.get("examples", [])[:3]:
            if isinstance(example, str):
                if " - " in example or " — " in example:
                    example = example.split(" - ")[0].split(" — ")[0].strip()
                example = re.sub(r"\([^)]*[а-яА-ЯёЁ][^)]*\)", "", example).strip()
                words = example.split()
                if len(words) > 15:
                    example = " ".join(words[:15])
                short_examples.append(example)

        return explanation, short_examples

    @staticmethod
    def determine_difficulty(
        current: DifficultyLevel | None,
        from_ai: str | None,
    ) -> str | None:
        if current:
            return current.value
        return infer_cefr_value_string_from_ai(from_ai)


class GroqWordAnalysisHelper:
    """Calls Groq and converts its response into WordAnalysisResponse."""

    @staticmethod
    def _extract_content(result: dict) -> str:
        content = result["choices"][0]["message"]["content"]
        return extract_fenced_llm_content(content)

    async def analyze_word(
        self,
        word: str,
        difficulty_level: DifficultyLevel | None,
        translation: str,
    ) -> WordAnalysisResponse:
        if not settings.GROQ_API_KEY:
            raise HTTPException(status_code=500, detail="Groq API key is not configured")

        prompt = AIAnalysisPromptHelper.build_prompt(word)
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.GROQ_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 300,
            "response_format": {"type": "json_object"},
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=502, detail=f"Groq API error: {str(exc)}")

        content = self._extract_content(result)
        analysis = json.loads(content)
        explanation, examples = AIAnalysisResponseHelper.clean_analysis_data(analysis)
        difficulty = AIAnalysisResponseHelper.determine_difficulty(
            difficulty_level,
            analysis.get("difficulty"),
        )

        return WordAnalysisResponse(
            word=word,
            translation=translation,
            explanation=explanation,
            examples=examples,
            difficulty=difficulty,
        )


class VocabularyLookupHelper:
    """Provides common-word lookup helpers for vocabulary services."""

    def __init__(self, db: AsyncSession):
        self.common_words = CommonWordRepository(db)

    async def get_word_level(self, word: str) -> DifficultyLevel | None:
        normalized = alphabetic_english_word_key(word)
        if not normalized:
            return None
        common_word = await self.common_words.get_by_word_text(normalized)
        return common_word.cefr_level if common_word else None

    async def get_common_words_by_level(
        self,
        level: DifficultyLevel,
        limit: int = 20,
        exclude_words: list[str] | None = None,
    ) -> list[str]:
        return await self.common_words.list_words_by_level(
            level=level,
            limit=limit,
            exclude_words=exclude_words,
        )

    async def is_word_common(self, word: str) -> bool:
        normalized = alphabetic_english_word_key(word)
        if not normalized:
            return False
        return await self.common_words.is_everyday_common(normalized)
