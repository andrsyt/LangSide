"""Pure rules: validate user translations for repeat exercises (no I/O)."""

from __future__ import annotations

from difflib import SequenceMatcher


class RepeatAnswerService:
    """Validates user translations for repeat exercises."""

    @staticmethod
    def check_translation_correctness(
        user_input: str,
        primary_translation: str | None,
        alternative_translations: list[str] | None = None,
    ) -> bool:
        if not primary_translation:
            return False

        normalized_input = user_input.strip().lower()
        primary = primary_translation.strip().lower()
        if normalized_input == primary:
            return True

        if alternative_translations:
            for alternative in alternative_translations:
                normalized_alternative = alternative.strip().lower()
                if normalized_input == normalized_alternative:
                    return True

                similarity = SequenceMatcher(
                    None,
                    normalized_input,
                    normalized_alternative,
                ).ratio()
                if similarity >= 0.85:
                    return True

        similarity = SequenceMatcher(None, normalized_input, primary).ratio()
        return similarity >= 0.85
