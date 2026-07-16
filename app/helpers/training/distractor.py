"""Heuristic distractor word selection for training exercises."""

from __future__ import annotations

import random
import re
from typing import Any


class TrainingDistractorHelper:
    """Contains validation and selection logic for distractor words."""

    DISTRACTOR_STOPWORDS: frozenset[str] = frozenset(
        {
            "a",
            "an",
            "the",
            "and",
            "or",
            "but",
            "if",
            "so",
            "as",
            "at",
            "by",
            "to",
            "of",
            "in",
            "on",
            "for",
            "from",
            "with",
            "into",
            "over",
            "after",
            "before",
            "than",
            "then",
            "that",
            "this",
            "these",
            "those",
            "it",
            "its",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "get",
            "got",
            "can",
            "could",
            "should",
            "would",
            "will",
            "just",
            "only",
            "also",
            "not",
            "no",
            "yes",
            "very",
            "too",
            "how",
            "what",
            "when",
            "where",
            "why",
            "who",
            "which",
            "my",
            "your",
            "his",
            "her",
            "their",
            "our",
            "some",
            "any",
            "each",
            "every",
            "both",
            "few",
            "more",
            "most",
            "other",
            "such",
            "same",
            "another",
            "much",
            "many",
            "little",
            "own",
            "last",
            "first",
            "next",
            "new",
            "old",
            "long",
            "big",
            "small",
            "good",
            "bad",
            "great",
            "right",
            "wrong",
            "true",
            "false",
            "here",
            "there",
            "now",
            "still",
            "even",
            "well",
            "back",
            "off",
            "out",
            "up",
            "down",
            "way",
            "all",
            "one",
            "two",
        }
    )
    WORD_RE = re.compile(r"^[a-zA-Z][a-zA-Z\-]*[a-zA-Z]$|^[a-zA-Z]$")

    @classmethod
    def _is_valid_token(cls, word: str) -> bool:
        normalized_word = word.strip()
        if len(normalized_word) < 4:
            return False
        if " " in normalized_word:
            return False
        return bool(cls.WORD_RE.match(normalized_word))

    @classmethod
    def is_plausible_ai_distractor(cls, candidate: str, target: str) -> bool:
        """Checks that an LLM distractor is a valid single-word token."""
        normalized_candidate = candidate.strip()
        normalized_target = target.strip()
        if (
            not normalized_candidate
            or not normalized_target
            or normalized_candidate.lower() == normalized_target.lower()
        ):
            return False
        if not cls._is_valid_token(normalized_candidate):
            return False
        if normalized_candidate.lower() in cls.DISTRACTOR_STOPWORDS:
            return False
        return True

    @classmethod
    def _is_good_distractor(cls, candidate: str, target: str) -> bool:
        normalized_candidate = candidate.strip()
        normalized_target = target.strip()
        if (
            not normalized_candidate
            or not normalized_target
            or normalized_candidate.lower() == normalized_target.lower()
        ):
            return False
        if not cls._is_valid_token(normalized_candidate):
            return False
        if normalized_candidate.lower() in cls.DISTRACTOR_STOPWORDS:
            return False
        target_length, candidate_length = len(normalized_target), len(
            normalized_candidate
        )
        if (
            candidate_length < max(4, target_length - 3)
            or candidate_length > target_length + 5
        ):
            return False
        return True

    @staticmethod
    def _score_length_closeness(candidate: str, target: str) -> int:
        return abs(len(candidate.strip()) - len(target.strip()))

    @classmethod
    def pick_two_distractor_words(
        cls,
        learning_items: list[Any],
        target_word: str,
        *,
        rng: random.Random | None = None,
    ) -> tuple[str, str]:
        randomizer = rng or random.Random()
        target = (target_word or "").strip()
        if not target:
            raise ValueError("target_word is empty")

        candidates: list[str] = []
        seen_lower: set[str] = set()
        for item in learning_items:
            word_text = (getattr(item, "word_text", None) or item or "").strip()
            if not word_text or word_text.lower() in seen_lower:
                continue
            if not cls._is_good_distractor(word_text, target):
                continue
            seen_lower.add(word_text.lower())
            candidates.append(word_text)

        if len(candidates) < 2:
            seen_lower.clear()
            candidates.clear()
            target_length = len(target)
            for item in learning_items:
                word_text = (getattr(item, "word_text", None) or item or "").strip()
                if not word_text or word_text.lower() == target.lower():
                    continue
                if not cls._is_valid_token(word_text):
                    continue
                if word_text.lower() in cls.DISTRACTOR_STOPWORDS:
                    continue
                if word_text.lower() in seen_lower:
                    continue
                if len(word_text) < 4 or len(word_text) > target_length + 8:
                    continue
                seen_lower.add(word_text.lower())
                candidates.append(word_text)

        if len(candidates) < 2:
            raise ValueError("not enough distractor candidates after filtering")

        candidates.sort(key=lambda word: cls._score_length_closeness(word, target))
        best = cls._score_length_closeness(candidates[0], target)
        tight = [
            word
            for word in candidates
            if cls._score_length_closeness(word, target) <= best + 2
        ]
        if len(tight) < 2:
            tight = [
                word
                for word in candidates
                if cls._score_length_closeness(word, target) <= best + 4
            ]
        if len(tight) < 2:
            tight = candidates

        randomizer.shuffle(tight)
        first = tight[0]
        second = next(
            (word for word in tight[1:] if word.lower() != first.lower()),
            None,
        )
        if second is None:
            raise ValueError("could not pick two distinct distractors")
        return first, second
