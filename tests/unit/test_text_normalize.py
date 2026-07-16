"""Test text normalization utilities."""

from app.helpers.text_utils import collapse_whitespace, normalize_translation, normalize_sentence, is_acceptable_translation


def test_collapse_whitespace():
    assert collapse_whitespace(None) == ""
    assert collapse_whitespace("") == ""
    assert collapse_whitespace("  hello  ") == "hello"
    assert collapse_whitespace("  hello  world  ") == "hello world"

def test_normalize_translation():
    assert normalize_translation(None) == ""
    assert normalize_translation("") == ""
    assert normalize_translation("hello") == "hello"
    assert normalize_translation("hello world") == "hello world"
    assert normalize_translation("hello world.") == "hello world"
    assert normalize_translation("HELLO world!?.") == "hello world!?"
    assert normalize_translation("HELLO world") == "hello world"
    

def test_normalize_sentence():
    assert normalize_sentence(None) == ""
    assert normalize_sentence("") == ""
    assert normalize_sentence("hello") == "Hello."
    assert normalize_sentence("hello world") == "Hello world."
    assert normalize_sentence("hello world", max_words=1) == "Hello."
    assert normalize_sentence("hello world", max_words=2) == "Hello world."
    assert normalize_sentence("hello world", max_words=3) == "Hello world."
    assert normalize_sentence("hello world", max_words=16) == "Hello world."
    assert normalize_sentence("hello world.", max_words=15) == "Hello world."


def test_is_acceptable_translation_rejects_empty():
    assert is_acceptable_translation(None, "hello") is False
    assert is_acceptable_translation("", "hello") is False
    assert is_acceptable_translation("   ", "hello") is False
    assert is_acceptable_translation(".", "hello") is False


def test_is_acceptable_translation_rejects_same_as_word():
    assert is_acceptable_translation("hello", "hello") is False
    assert is_acceptable_translation("Hello", "hello") is False
    assert is_acceptable_translation("  HELLO  ", "hello") is False


def test_is_acceptable_translation_rejects_too_long():
    assert is_acceptable_translation("abcdef", "x", max_len=3) is False
    assert is_acceptable_translation("a" * 81, "x") is False


def test_is_acceptable_translation_accepts_valid():
    assert is_acceptable_translation("привіт", "hello") is True
    assert is_acceptable_translation("яблуко", "apple") is True
    assert is_acceptable_translation("abc", "x", max_len=3) is True