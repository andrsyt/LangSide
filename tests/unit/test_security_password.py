"""Unit tests: password hashing."""

from app.core.security import hash_password, verify_password


def test_hash_and_verify_password() -> None:
    hashed = hash_password("my-secret-pass")
    assert hashed != "my-secret-pass"
    assert verify_password("my-secret-pass", hashed) is True
    assert verify_password("wrong", hashed) is False
