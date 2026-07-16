"""Shuffling and neighbor alignment for training UI options."""

from __future__ import annotations

import random
from typing import Any

from app.helpers.text_utils import canonical_english_word_key


class TrainingOptionHelper:
    """Helper methods for training options."""

    @staticmethod
    def shuffle_context_variants(context_variants: list[str]) -> tuple[list[str], int]:
        indexed = list(enumerate(context_variants))
        random.shuffle(indexed)
        shuffled = [value for _, value in indexed]
        correct_index = next(i for i, (orig, _) in enumerate(indexed) if orig == 0)
        return shuffled, correct_index

    @staticmethod
    def neighbor_word_ids_from_texts(
        d1_text: str,
        d2_text: str,
        learning_words: list[Any],
    ) -> tuple[int | None, int | None]:
        lut = {
            canonical_english_word_key(getattr(w, "word_text", "") or ""): w.id
            for w in learning_words
        }
        return (
            lut.get(canonical_english_word_key(d1_text)),
            lut.get(canonical_english_word_key(d2_text)),
        )

    @staticmethod
    def shuffle_sentence_neighbor_aligned(
        three_sentences: list[str],
        neighbor_ids_ordered: list[int | None],
    ) -> tuple[list[str], list[int | None], int]:
        pairs = list(zip(three_sentences, neighbor_ids_ordered))
        indexed = list(enumerate(pairs))
        random.shuffle(indexed)
        shuffled_s = [p[1][0] for p in indexed]
        shuffled_n = [p[1][1] for p in indexed]
        correct_idx = next(i for i, (orig, _) in enumerate(indexed) if orig == 0)
        return shuffled_s, shuffled_n, correct_idx

    _shuffle_context_variants = shuffle_context_variants
    _neighbor_word_ids_from_texts = neighbor_word_ids_from_texts
    _shuffle_sentence_neighbor_aligned = shuffle_sentence_neighbor_aligned
