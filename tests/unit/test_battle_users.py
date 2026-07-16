"""Unit tests: battle user display rules."""

from app.helpers.battle.users import is_eligible_battle_user, public_display_name
from app.models.user import User


def _user(**kwargs) -> User:
    return User(
        id=1,
        public_id=1_000_001,
        email=kwargs.get("email", "real@example.com"),
        username=kwargs.get("username", "player1"),
        hashed_password="x",
        is_anonymous=kwargs.get("is_anonymous", False),
    )


def test_anonymous_not_eligible() -> None:
    assert is_eligible_battle_user(_user(is_anonymous=True)) is False


def test_guest_email_not_eligible() -> None:
    assert is_eligible_battle_user(_user(email="anon_x@guest.local")) is False


def test_real_user_display_name() -> None:
    assert public_display_name(_user(username="MyUser")) == "MyUser"


def test_ineligible_gets_fallback() -> None:
    assert public_display_name(_user(is_anonymous=True)) == "Player"
