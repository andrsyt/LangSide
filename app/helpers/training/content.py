"""Training content: examples, synonyms CSV, association display."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from app.helpers.text_utils import canonical_english_word_key
from .association import TrainingAssociationHelper
from app.models.training import Training

_BASE_DIR = Path(__file__).resolve().parents[3]
_SYNONYMS_CSV = _BASE_DIR / "localization" / "word_synonyms.csv"


class TrainingContentHelper:
    """Helper methods for training content."""

    @staticmethod
    def parse_examples(raw: str | None) -> list[str]:
        if not raw or not raw.strip():
            return []
        raw = raw.strip()
        if raw.startswith("["):
            try:
                data = json.loads(raw)
                return data if isinstance(data, list) else []
            except json.JSONDecodeError:
                pass
        return [line.strip() for line in raw.split("\n") if line.strip()]

    @staticmethod
    def get_synonyms_by_word_text(word_text: str) -> list[str]:
        if not word_text or not _SYNONYMS_CSV.is_file():
            return []
        key = canonical_english_word_key(word_text)
        with open(_SYNONYMS_CSV, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if canonical_english_word_key(row.get("word", "")) == key:
                    raw = row.get("synonyms", "").strip()
                    if not raw:
                        return []
                    return [s.strip() for s in raw.split("|") if s.strip()]
        return []

    @staticmethod
    def collect_display_associations(training: Training | None) -> list[str]:
        if training is None:
            return []

        freeform = training.freeform_associations
        if freeform is None and training.user_association:
            freeform = TrainingAssociationHelper.extract_legacy_user_associations(
                list(training.user_association)
            )

        return TrainingAssociationHelper.extract_card_association_lines(
            freeform,
            training.association_v2_data,
        )

    @staticmethod
    def can_complete_training(training: Training | None) -> bool:
        if training is None:
            return False
        anchor_data = training.semantic_anchor_data or {}
        has_anchor = bool(anchor_data)
        if has_anchor and not anchor_data.get("is_context_correct"):
            return False
        has_memory_link = bool(
            TrainingContentHelper.collect_display_associations(training)
        )
        if not has_anchor or not has_memory_link:
            return False
        if training.association_v2_data:
            completed = list(training.completed_quest_types or [])
            if "association_recall" not in completed:
                return False
        return True

    _parse_examples = parse_examples
    _get_synonyms_by_word_text = get_synonyms_by_word_text
    _collect_display_associations = collect_display_associations
    _can_complete_training = can_complete_training
