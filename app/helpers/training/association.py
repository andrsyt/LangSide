"""Association payloads and legacy anchor/user association lines."""

from __future__ import annotations

from app.helpers.text_utils import strip_nonempty_strings


def _association_v2_triple(payload: dict | None) -> tuple[str, str, str]:
    if not payload:
        return "", "", ""
    image = str(payload.get("image") or "").strip()
    action = str(payload.get("action") or "").strip()
    emotion = str(payload.get("emotion") or "").strip()
    return image, action, emotion


class TrainingAssociationHelper:
    """Helper methods for training association payloads and legacy values."""

    @staticmethod
    def is_system_association(value: str) -> bool:
        return value.startswith("anchor:") or value.startswith(
            "anchor_context_correct:"
        )

    @classmethod
    def split_associations(cls, values: list[str]) -> tuple[list[str], list[str]]:
        system_associations: list[str] = []
        user_associations: list[str] = []
        for value in values:
            if cls.is_system_association(value):
                system_associations.append(value)
            else:
                user_associations.append(value)
        return system_associations, user_associations

    @staticmethod
    def normalize_freeform_associations(values: list[str] | None) -> list[str]:
        return strip_nonempty_strings(values)

    @classmethod
    def merge_legacy_system_with_user(
        cls,
        existing: list[str],
        new_user: list[str],
    ) -> list[str]:
        system_existing, _ = cls.split_associations(existing)
        normalized_new_user = cls.normalize_freeform_associations(new_user)
        return system_existing + normalized_new_user

    @classmethod
    def extract_legacy_user_associations(cls, values: list[str]) -> list[str]:
        _, user_associations = cls.split_associations(values)
        return user_associations

    @staticmethod
    def association_v2_to_text(payload: dict | None) -> str | None:
        image, action, emotion = _association_v2_triple(payload)
        parts = [part for part in [image, action, emotion] if part]
        if not parts:
            return None
        return " | ".join(parts)

    @staticmethod
    def build_association_recall_cue(payload: dict | None) -> str | None:
        image, action, emotion = _association_v2_triple(payload)
        cue_parts = [part for part in [image, emotion] if part]
        if len(cue_parts) < 2:
            cue_parts = [part for part in [image, action, emotion] if part]
        if not cue_parts:
            return None
        return " ; ".join(cue_parts)

    @classmethod
    def extract_card_association_lines(
        cls,
        freeform_values: list[str] | None,
        association_v2_payload: dict | None,
    ) -> list[str]:
        lines = cls.normalize_freeform_associations(freeform_values)
        association_v2_text = cls.association_v2_to_text(association_v2_payload)
        if association_v2_text:
            lines.append(association_v2_text)
        return lines
