import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models.user import User
from app.services.admin_account import ensure_admin_account
from app.utils.auth_security import verify_password


@pytest.fixture
def db():
    engine = create_engine("sqlite://")
    User.__table__.create(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


def test_admin_setup_is_idempotent_and_hashes_password(db):
    password = "a-long-administrator-password"
    user = ensure_admin_account(db, "ADMIN@example.com", password)
    original_hash = user.password_hash
    assert user.email == "admin@example.com"
    assert user.is_admin and original_hash != password
    assert verify_password(password, original_hash)
    ensure_admin_account(db, user.email, password)
    assert db.query(User).count() == 1
    assert user.password_hash == original_hash


def test_setup_cannot_take_over_existing_account_with_different_password(db):
    user = ensure_admin_account(db, "admin@example.com", "original-long-password")
    user.is_admin = False
    db.commit()
    with pytest.raises(ValueError, match="does not match"):
        ensure_admin_account(db, user.email, "different-long-password")
    db.refresh(user)
    assert not user.is_admin
    assert verify_password("original-long-password", user.password_hash)


def test_setup_rejects_short_password_before_creating_account(db):
    with pytest.raises(ValueError, match="at least 16"):
        ensure_admin_account(db, "admin@example.com", "short")
    assert db.query(User).count() == 0
