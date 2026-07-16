"""Sentence context and word substitution for training exercises."""

from __future__ import annotations

import re


class TrainingContextHelper:
    """Helper methods for contextual training sentence generation."""

    @staticmethod
    def inject_word_in_sentence(sentence: str, word: str) -> str:
        normalized_word = (word or "").strip()
        normalized_sentence = (sentence or "").strip()

        if not normalized_word:
            return normalized_sentence

        if re.search(
            rf"\b{re.escape(normalized_word)}\b",
            normalized_sentence,
            flags=re.IGNORECASE,
        ):
            return normalized_sentence

        if not normalized_sentence:
            return f"I need to use «{normalized_word}» in a sentence."

        return f"{normalized_sentence} «{normalized_word}» fits this meaning."

    @classmethod
    def build_three_similar_sentences(
        cls,
        target_word: str,
        base_sentence: str,
        distractor_a: str,
        distractor_b: str,
    ) -> tuple[list[str], int]:
        base = cls.inject_word_in_sentence(base_sentence, target_word)
        correct = cls.swap_target_word(base, target_word, target_word)
        wrong1 = cls.swap_target_word(base, target_word, distractor_a)
        wrong2 = cls.swap_target_word(base, target_word, distractor_b)
        return [correct, wrong1, wrong2], 0

    @staticmethod
    def _adjust_case_like(model: str, replacement: str) -> str:
        normalized_replacement = (replacement or "").strip()
        if not model or not normalized_replacement:
            return normalized_replacement
        if model.isupper():
            return normalized_replacement.upper()
        if len(model) > 1 and model[0].isupper() and model[1:].islower():
            return normalized_replacement.capitalize()
        if model[0].isupper():
            if len(normalized_replacement) > 1:
                return (
                    normalized_replacement[0].upper()
                    + normalized_replacement[1:].lower()
                )
            return normalized_replacement.upper()
        return normalized_replacement.lower()

    @classmethod
    def swap_target_word(
        cls,
        sentence: str,
        target: str,
        replacement: str,
    ) -> str:
        text = (sentence or "").strip()
        normalized_target = (target or "").strip()
        normalized_replacement = (replacement or "").strip()
        if not text or not normalized_target:
            return text

        pattern = re.compile(
            rf"\b{re.escape(normalized_target)}\b",
            flags=re.IGNORECASE,
        )

        def _one_sub(match: re.Match) -> str:
            return cls._adjust_case_like(match.group(0), normalized_replacement)

        new_text, substitutions = pattern.subn(_one_sub, text, count=1)
        if substitutions > 0:
            return new_text

        return f"{text} ({normalized_replacement})"
