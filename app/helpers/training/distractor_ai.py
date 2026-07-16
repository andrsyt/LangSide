"""Groq-backed context distractors with Redis cache."""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

import httpx

from app.core.config import settings
from app.helpers.text_utils import (
    canonical_english_word_key,
    extract_fenced_llm_content,
    strip_nonempty_strings,
)
from .context import TrainingContextHelper
from .distractor import TrainingDistractorHelper
from app.services.cache_service import get_cache, set_cache

logger = logging.getLogger(__name__)

_CACHE_PREFIX = "training_ctx_distractors:"
_CACHE_TTL_SECONDS = 86_400


class TrainingDistractorAIHelper:
    """Fetches and validates AI-generated distractors for sentence exercises."""

    @staticmethod
    def cache_key(sentence: str, target: str) -> str:
        raw = f"{sentence.strip()}|{canonical_english_word_key(target)}"
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:40]
        return f"{_CACHE_PREFIX}{digest}"

    @staticmethod
    def normalize_groq_words(data: dict[str, Any]) -> list[str]:
        raw = data.get("wrong_words")
        if raw is None:
            raw = data.get("wrongWords")
        if not isinstance(raw, list):
            return []

        strings_only = [item for item in raw[:4] if isinstance(item, str)]
        return strip_nonempty_strings(strings_only)

    @staticmethod
    def ai_pair_produces_three_distinct(
        target_word: str,
        base_sentence: str,
        first_word: str,
        second_word: str,
    ) -> bool:
        try:
            variants, _ = TrainingContextHelper.build_three_similar_sentences(
                target_word,
                base_sentence,
                first_word,
                second_word,
            )
        except Exception:
            return False

        if len(variants) != 3:
            return False
        return len({variant.strip() for variant in variants}) == 3

    @classmethod
    async def fetch_context_distractors_from_groq(
        cls,
        sentence: str,
        target_word: str,
    ) -> tuple[str, str] | None:
        if not settings.GROQ_API_KEY:
            return None

        target = (target_word or "").strip()
        sent = (sentence or "").strip()
        if not target or not sent:
            return None

        cache_key = cls.cache_key(sent, target)
        cached = get_cache(cache_key)
        if cached:
            try:
                data = json.loads(cached)
                words = cls.normalize_groq_words(data)
                if len(words) >= 2:
                    first_word, second_word = words[0], words[1]
                    if (
                        TrainingDistractorHelper.is_plausible_ai_distractor(
                            first_word, target
                        )
                        and TrainingDistractorHelper.is_plausible_ai_distractor(
                            second_word, target
                        )
                        and canonical_english_word_key(first_word)
                        != canonical_english_word_key(second_word)
                        and cls.ai_pair_produces_three_distinct(
                            target,
                            sent,
                            first_word,
                            second_word,
                        )
                    ):
                        return (first_word, second_word)
            except (json.JSONDecodeError, TypeError):
                pass

        prompt = f"""You build a multiple-choice English exercise.

Sentence: {sent!r}
Target word (must be judged as correct ONLY in the original sentence above): {target!r}

Pick exactly TWO different single English words for a "wrong answer" exercise:
1) Each can grammatically replace "{target}" in the same position in the sentence (same slot).
2) They must NOT be synonyms of "{target}" — using them should change or break the intended meaning in THIS context.
3) Prefer words a learner might confuse with "{target}" or that sound plausible but are wrong here (not random comedy nouns like "tomato" unless the sentence truly allows that confusion).

Rules for the two words: letters and optional hyphen only, no spaces, no phrases, 4–12 characters, not the target word.

Return ONLY valid JSON:
{{"wrong_words": ["word1", "word2"]}}
"""

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {
            "model": settings.GROQ_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.25,
            "max_tokens": 150,
            "response_format": {"type": "json_object"},
        }

        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            logger.warning("Groq context distractors failed: %s", exc)
            return None

        content = extract_fenced_llm_content(
            result["choices"][0]["message"]["content"],
        )

        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            logger.warning("Groq context distractors: invalid JSON")
            return None

        words = cls.normalize_groq_words(data)
        if len(words) < 2:
            return None

        first_word, second_word = words[0], words[1]
        if not TrainingDistractorHelper.is_plausible_ai_distractor(
            first_word,
            target,
        ) or not TrainingDistractorHelper.is_plausible_ai_distractor(
            second_word,
            target,
        ):
            return None
        if canonical_english_word_key(first_word) == canonical_english_word_key(
            second_word,
        ):
            return None
        if not cls.ai_pair_produces_three_distinct(
            target,
            sent,
            first_word,
            second_word,
        ):
            return None

        set_cache(
            cache_key,
            json.dumps({"wrong_words": [first_word, second_word]}),
            ttl=_CACHE_TTL_SECONDS,
        )
        return (first_word, second_word)


async def fetch_context_distractors_from_groq(
    sentence: str,
    target_word: str,
) -> tuple[str, str] | None:
    return await TrainingDistractorAIHelper.fetch_context_distractors_from_groq(
        sentence,
        target_word,
    )
