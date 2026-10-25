import pytest
from pydantic import ValidationError

from app.api.auth import Credentials, RegistrationCredentials


def test_login_accepts_existing_short_password():
    assert Credentials(email="test@123.com", password="test").password == "test"


def test_login_rejects_empty_password():
    with pytest.raises(ValidationError):
        Credentials(email="test@123.com", password="")


def test_registration_still_requires_eight_characters():
    with pytest.raises(ValidationError):
        RegistrationCredentials(email="test@123.com", password="test")
    assert RegistrationCredentials(email="test@123.com", password="eight123").password == "eight123"
