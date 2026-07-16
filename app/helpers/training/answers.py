"""Answer checking for training exercises."""

from __future__ import annotations

import re

from app.helpers.battle.text import normalize_answer
from app.helpers.text_utils import strip_lower_nonempty_strings
from app.schemas.training import SynonymsRecallResult


class TrainingAnswerHelper:
    """Helper methods for training answers."""

    @staticmethod
    def check_english_word_answer(user_answer: str, correct_word: str) -> bool:
        """Active recall: user must type the English headword, not the translation gloss."""
        if not user_answer or not user_answer.strip():
            return False
        cw = (correct_word or "").strip()
        if not cw:
            return False
        u = user_answer.strip().lower().strip('.,!?;:"\'')
        return u == cw.lower()

    @staticmethod
    def _levenshtein_distance(left: str, right: str) -> int:
        if left == right:
            return 0
        if not left:
            return len(right)
        if not right:
            return len(left)
        prev = list(range(len(right) + 1))
        for i, char_left in enumerate(left, start=1):
            current = [i]
            for j, char_right in enumerate(right, start=1):
                cost = 0 if char_left == char_right else 1
                current.append(
                    min(
                        current[j - 1] + 1,
                        prev[j] + 1,
                        prev[j - 1] + cost,
                    )
                )
            prev = current
        return prev[-1]

    @classmethod
    def check_english_word_answer_relaxed(cls, user_answer: str, correct_word: str) -> bool:
        """Exact match or small typo tolerance for recall exercises."""
        if cls.check_english_word_answer(user_answer, correct_word):
            return True
        normalized_user = normalize_answer(user_answer)
        normalized_target = normalize_answer(correct_word)
        if not normalized_user or not normalized_target:
            return False
        max_distance = 1 if len(normalized_target) <= 5 else 2
        if abs(len(normalized_user) - len(normalized_target)) > max_distance:
            return False
        return cls._levenshtein_distance(normalized_user, normalized_target) <= max_distance

    @staticmethod
    def check_translation_relaxed(
        user_answer: str,
        correct_word: str,
        translation_gloss: str,
    ) -> bool:
        """
        Exact English word or "in my own words": parts of the translation hint are present in the answer.
        """
        if not user_answer or not (user_answer.strip()):
            return False
        cw = (correct_word or "").strip()
        if not cw:
            return False
        u = user_answer.strip().lower()
        target = cw.lower()
        if u == target:
            return True
        if u.strip('.,!?;:"\'') == target:
            return True
        gloss = (translation_gloss or "").strip().lower()
        if not gloss:
            return False
        for part in re.split(r"[,;/|]", gloss):
            p = part.strip()
            if len(p) >= 3 and p in u:
                return True
        gloss_tokens = [w for w in gloss.split() if len(w) >= 3]
        if gloss_tokens and any(w in u for w in gloss_tokens):
            return True
        return False

    @staticmethod
    def sentence_contains_word(sentence: str, word: str, *, min_length: int = 12) -> bool:
        text = (sentence or "").strip()
        target = (word or "").strip()
        if len(text) < min_length or not target:
            return False
        pattern = re.compile(rf"\b{re.escape(target)}\b", flags=re.IGNORECASE)
        return bool(pattern.search(text))

    @staticmethod
    def check_synonyms_recall_answer(
        user_answer: list[str],
        expected_synonyms: list[str],
        min_correct: int,
    ) -> SynonymsRecallResult:
        normalized_user_answer = strip_lower_nonempty_strings(user_answer)
        normalized_expected_synonyms = strip_lower_nonempty_strings(expected_synonyms)
        user_set = set(normalized_user_answer)
        expected_set = set(normalized_expected_synonyms)
        correct_matches = user_set & expected_set
        missed = expected_set - user_set
        is_correct = len(correct_matches) >= min_correct if min_correct > 0 else False
        return SynonymsRecallResult(
            correct=is_correct,
            correct_synonyms=list(correct_matches),
            incorrect_synonyms=list(missed),
        )

    _check_translation_relaxed = check_translation_relaxed
    _check_synonyms_recall_answer = check_synonyms_recall_answer
