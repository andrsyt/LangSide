"""Groq-backed personalized semantic-anchor prompt starters."""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

import httpx

from app.core.language_codes import default_language_code
from app.core.config import settings
from app.helpers.text_utils import extract_fenced_llm_content, strip_nonempty_strings
from app.services.cache_service import get_cache, set_cache

logger = logging.getLogger(__name__)

_CACHE_PREFIX = "training_anchor_prompts:"
_CACHE_TTL_SECONDS = 86_400
_ANCHOR_MAX_LEN = 60

# Localized fallback starters (used when Groq is unavailable / returns garbage).
# Each line references the word or its translation and ends with "..." so the
# learner continues in their own words.
_FALLBACK_TEMPLATES: dict[str, list[str]] = {
    "uk": [
        "Ситуація з «{word}»...",
        "Емоція від «{gloss}»...",
        "Образ для «{word}»...",
    ],
    "ru": [
        "Ситуация с «{word}»...",
        "Эмоция от «{gloss}»...",
        "Образ для «{word}»...",
    ],
    "en": [
        'A real situation with "{word}"...',
        'A feeling from "{word}"...',
        'A vivid image of "{word}"...',
    ],
    # Legacy keys kept for cached payloads / older clients.
    "ukrainian": [
        "Ситуація з «{word}»...",
        "Емоція від «{gloss}»...",
        "Образ для «{word}»...",
    ],
    "russian": [
        "Ситуация с «{word}»...",
        "Эмоция от «{gloss}»...",
        "Образ для «{word}»...",
    ],
    "english": [
        'A real situation with "{word}"...',
        'A feeling from "{word}"...',
        'A vivid image of "{word}"...',
    ],
}


def _is_valid_anchor(
    prompt: str,
    *,
    word_text: str,
    translation_gloss: str,
    max_len: int = _ANCHOR_MAX_LEN,
) -> bool:
    """An anchor starter is valid if it is short, not a question, and tied to the word."""
    p = prompt.strip()
    if not p:
        return False
    if len(p) > max_len:
        return False
    if p.endswith("?"):
        return False

    lowered = p.lower()
    word = word_text.strip().lower()
    gloss = translation_gloss.strip().lower()
    if word and word in lowered:
        return True
    if gloss and gloss in lowered:
        return True
    return False


class TrainingAnchorAIHelper:
    @staticmethod
    def cache_key(word_text: str, explanation: str, translation: str) -> str:
        raw = f"{word_text.strip()}|{explanation.strip()}|{translation.strip()}"
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:40]
        return f"{_CACHE_PREFIX}{digest}"

    @staticmethod
    def normalize_prompts(
        data: dict[str, Any],
        *,
        word_text: str,
        translation_gloss: str,
    ) -> list[str]:
        raw = data.get("anchor_prompts")
        if raw is None:
            raw = data.get("anchorPrompts")
        if not isinstance(raw, list):
            return []
        prompts = strip_nonempty_strings([str(item) for item in raw[:3]])
        return [
            prompt
            for prompt in prompts
            if _is_valid_anchor(
                prompt,
                word_text=word_text,
                translation_gloss=translation_gloss,
            )
        ]

    @classmethod
    async def fetch_anchor_prompts_from_groq(
        cls,
        *,
        word_text: str,
        explanation: str,
        translation_gloss: str,
        learner_language: str,
    ) -> list[str] | None:
        if not settings.GROQ_API_KEY:
            return None

        word = (word_text or "").strip()
        if not word:
            return None

        expl = (explanation or "").strip() or "General vocabulary word."
        gloss = (translation_gloss or "").strip()
        lang = (learner_language or default_language_code()).strip()

        cache_key = cls.cache_key(word, expl, gloss)
        cached = get_cache(cache_key)
        if cached:
            try:
                data = json.loads(cached)
                prompts = cls.normalize_prompts(
                    data,
                    word_text=word,
                    translation_gloss=gloss,
                )
                if len(prompts) == 3:
                    return prompts
            except (json.JSONDecodeError, TypeError):
                pass

        prompt = f"""Create exactly THREE short memory-hook STARTERS for an English learner studying the word "{word}".

Learner interface language: {lang}
Translation hint: {gloss or "(unknown)"}
Meaning: {expl}

Each starter must:
- Be one sentence, max 60 characters, in {lang} (not English).
- Mention the word "{word}" or its translation "{gloss or word}".
- Suggest a different hook type: (1) real-life situation, (2) emotion/feeling, (3) vivid image.
- Be specific to THIS word's meaning — not generic study tips.
- End with "..." so the user continues in their own words.
- Do NOT end with a question mark.

Return ONLY JSON:
{{"anchor_prompts": ["...", "...", "..."]}}
"""

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {
            "model": settings.GROQ_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.4,
            "max_tokens": 280,
            "response_format": {"type": "json_object"},
        }

        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            logger.warning("Groq anchor prompts failed: %s", exc)
            return None

        content = extract_fenced_llm_content(
            result["choices"][0]["message"]["content"],
        )
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            logger.warning("Groq anchor prompts: invalid JSON")
            return None

        prompts = cls.normalize_prompts(
            data,
            word_text=word,
            translation_gloss=gloss,
        )
        if len(prompts) != 3:
            return None

        set_cache(cache_key, json.dumps({"anchor_prompts": prompts}), ttl=_CACHE_TTL_SECONDS)
        return prompts


async def fetch_anchor_prompts_from_groq(
    *,
    word_text: str,
    explanation: str,
    translation_gloss: str,
    learner_language: str,
) -> list[str] | None:
    return await TrainingAnchorAIHelper.fetch_anchor_prompts_from_groq(
        word_text=word_text,
        explanation=explanation,
        translation_gloss=translation_gloss,
        learner_language=learner_language,
    )


def default_anchor_prompts(
    word_text: str,
    translation_gloss: str = "",
    learner_language: str | None = None,
) -> list[str]:
    word = (word_text or "").strip()
    gloss = (translation_gloss or "").strip() or word
    lang = (learner_language or default_language_code()).strip().lower()
    templates = _FALLBACK_TEMPLATES.get(lang) or _FALLBACK_TEMPLATES["en"]
    return [template.format(word=word, gloss=gloss) for template in templates]
