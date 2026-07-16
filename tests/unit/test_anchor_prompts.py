"""Test semantic-anchor prompt validation and localized fallbacks."""

from app.helpers.training.anchor_ai import (
    TrainingAnchorAIHelper,
    _is_valid_anchor,
    default_anchor_prompts,
)


def test_is_valid_anchor_rejects_empty():
    assert _is_valid_anchor("", word_text="run", translation_gloss="бег") is False
    assert _is_valid_anchor("   ", word_text="run", translation_gloss="бег") is False


def test_is_valid_anchor_rejects_too_long():
    long_prompt = "run " + "x" * 80
    assert _is_valid_anchor(long_prompt, word_text="run", translation_gloss="бег") is False
    assert _is_valid_anchor("run " + "x" * 4, word_text="run", translation_gloss="бег", max_len=5) is False


def test_is_valid_anchor_rejects_question():
    assert _is_valid_anchor("Where do you run?", word_text="run", translation_gloss="бег") is False


def test_is_valid_anchor_rejects_unrelated():
    assert _is_valid_anchor("A generic study tip...", word_text="run", translation_gloss="бег") is False


def test_is_valid_anchor_accepts_with_word():
    assert _is_valid_anchor("Ситуация с run на работе...", word_text="run", translation_gloss="бег") is True


def test_is_valid_anchor_accepts_with_gloss():
    assert _is_valid_anchor("Образ для слова бег...", word_text="run", translation_gloss="бег") is True


def test_normalize_prompts_filters_invalid():
    data = {
        "anchor_prompts": [
            "Ситуация с run утром...",          # valid (word)
            "Generic motivational tip...",       # invalid (unrelated)
            "Эмоция от бег после финиша...",     # valid (gloss)
        ]
    }
    result = TrainingAnchorAIHelper.normalize_prompts(
        data, word_text="run", translation_gloss="бег"
    )
    assert result == ["Ситуация с run утром...", "Эмоция от бег после финиша..."]


def test_normalize_prompts_supports_camelcase_key():
    data = {"anchorPrompts": ["Образ run в парке..."]}
    result = TrainingAnchorAIHelper.normalize_prompts(
        data, word_text="run", translation_gloss="бег"
    )
    assert result == ["Образ run в парке..."]


def test_normalize_prompts_non_list_returns_empty():
    assert TrainingAnchorAIHelper.normalize_prompts(
        {"anchor_prompts": "oops"}, word_text="run", translation_gloss="бег"
    ) == []
    assert TrainingAnchorAIHelper.normalize_prompts(
        {}, word_text="run", translation_gloss="бег"
    ) == []


def test_default_anchor_prompts_localized():
    for lang in ("uk", "ru", "en"):
        prompts = default_anchor_prompts("run", "бег", lang)
        assert len(prompts) == 3
        for prompt in prompts:
            assert "run" in prompt or "бег" in prompt


def test_default_anchor_prompts_unknown_lang_falls_back_to_english():
    assert default_anchor_prompts("run", "бег", "klingon") == default_anchor_prompts(
        "run", "бег", "en"
    )


def test_default_anchor_prompts_uses_word_when_gloss_missing():
    prompts = default_anchor_prompts("run", "", "english")
    assert len(prompts) == 3
    for prompt in prompts:
        assert "run" in prompt
