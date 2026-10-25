"""Provision an explicitly configured administrator without storing plaintext passwords."""
from app.models.user import User
from app.utils.auth_security import hash_password, verify_password


def ensure_admin_account(db, email: str, password: str):
    email = email.strip().lower()
    if "@" not in email or len(password) < 16:
        raise ValueError("Administrator configuration requires an email and a password of at least 16 characters.")
    user = db.query(User).filter_by(email=email).first()
    if user is None:
        user = User(email=email, password_hash=hash_password(password), is_admin=True)
        db.add(user)
    elif not verify_password(password, user.password_hash):
        raise ValueError("Configured administrator password does not match the existing account.")
    else:
        user.is_admin = True
    db.commit()
    return user
