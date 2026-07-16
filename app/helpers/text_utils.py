"""Shared text utilities: word keys, CEFR parsing, LLM fences, string lists."""

from __future__ import annotations

import re

from app.models.word import DifficultyLevel

# --- English word keys ---


def canonical_english_word_key(value: str | None) -> str:
    """Lowercased trimmed surface form (user input, quest keys, CSV rows)."""
    return (value or "").strip().lower()


def alphabetic_english_word_key(word: str) -> str:
    """Letters and apostrophe only, lowercased — for common-word DB lookups."""
    return re.sub(r"[^a-zA-Z']", "", (word or "").strip().lower())


# --- CEFR ---

_FULL_CODE = re.compile(r"(A1|A2|B1|B2|C1|C2)")
_RELAXED_CODE = re.compile(r"([ABC][12])")
_LETTER_ONLY = re.compile(r"\b([ABC])\b")

_LETTER_FALLBACK = {
    "A": DifficultyLevel.A2,
    "B": DifficultyLevel.B2,
    "C": DifficultyLevel.C2,
}


def normalize_cefr_input(value: str) -> str:
    return value.strip().upper().replace(" ", "")


def parse_explicit_cefr_level(normalized: str) -> DifficultyLevel | None:
    """Match a full CEFR code (A1–C2) inside normalized text."""
    match = _FULL_CODE.search(normalized)
    if not match:
        return None
    return DifficultyLevel(match.group(1))


def infer_cefr_value_string_from_ai(from_ai: str | None) -> str | None:
    """
    Parse difficulty from loose AI text (may include extra words or a lone A/B/C).
    Returns enum .value string or None.
    """
    if not from_ai:
        return None
    raw = normalize_cefr_input(from_ai)
    match = _RELAXED_CODE.search(raw)
    if match:
        try:
            return DifficultyLevel(match.group(1)).value
        except ValueError:
            return None

    letter_only = _LETTER_ONLY.search(raw)
    if letter_only:
        return _LETTER_FALLBACK[letter_only.group(1)].value
    return None


# --- LLM markdown ---


def extract_fenced_llm_content(content: str) -> str:
    """Return JSON or code inside markdown fences, or the raw content if none."""
    if "```json" in content:
        return content.split("```json", 1)[1].split("```", 1)[0].strip()
    if "```" in content:
        return content.split("```", 1)[1].split("```", 1)[0].strip()
    return content


# --- String lists ---


def strip_nonempty_strings(values: list[str] | None) -> list[str]:
    """Strip each string and drop empty entries."""
    if not values:
        return []
    return [v.strip() for v in values if v and v.strip()]


def strip_lower_nonempty_strings(values: list[str]) -> list[str]:
    """Strip, lowercase, drop empty."""
    if not values:
        return []
    return [v.strip().lower() for v in values if v and v.strip()]


# --- Content normalization (translation / explanation / example) ---

def collapse_whitespace(value: str | None) -> str:
    if value is None:
        return ""

    value = re.sub(r'\s+', ' ', value).strip()

    return value


def normalize_translation(value: str | None) -> str:
    value = collapse_whitespace(value).lower()

    if len(value.split()) <=3:
        value = value.rstrip(".").strip()
    return value


def normalize_sentence(value: str | None, *, max_words: int | None = None) -> str:
    if value is None:
        return ""

    value = collapse_whitespace(value)

    if not value:
        return ""

    if max_words is not None and len(value.split()) > max_words:
        value = " ".join(value.split()[:max_words])

    result = value[0].upper() + value[1:]

    if not result.endswith((".", "!", "?")):
        result += "."

    return result


def is_acceptable_translation(translation: str | None, word_text: str, *, max_len: int = 80) -> bool:
    normalized = normalize_translation(translation)
    
    if not normalized:
        return False

    if normalized == word_text.strip().lower():
        return False

    if len(normalized) > max_len:
        return False

    return True