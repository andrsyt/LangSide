from __future__ import annotations


def normalize_answer(value: str) -> str:
    return value.strip().lower().strip('.,!?;:"\'')
