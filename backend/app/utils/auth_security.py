"""Dependency-free password and signed-token helpers for local accounts."""

import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone

from app.core.config import settings


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    iterations = 260_000
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return "pbkdf2_sha256${}${}${}".format(
        iterations,
        base64.urlsafe_b64encode(salt).decode("ascii"),
        base64.urlsafe_b64encode(digest).decode("ascii"),
    )


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, raw_iterations, raw_salt, raw_digest = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), base64.urlsafe_b64decode(raw_salt), int(raw_iterations),
        )
        return hmac.compare_digest(digest, base64.urlsafe_b64decode(raw_digest))
    except (ValueError, TypeError):
        return False


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def create_access_token(user_id: int, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=settings.AUTH_TOKEN_EXPIRE_HOURS)).timestamp()),
    }
    body = _b64(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = _b64(hmac.new(settings.AUTH_SECRET_KEY.encode("utf-8"), body.encode("ascii"), hashlib.sha256).digest())
    return f"{body}.{signature}"


def decode_access_token(token: str) -> dict | None:
    """Verify our compact signed token without adding a JWT dependency."""
    try:
        body, signature = token.split(".", 1)
        expected = _b64(hmac.new(settings.AUTH_SECRET_KEY.encode("utf-8"), body.encode("ascii"), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            return None
        padded = body + "=" * (-len(body) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded.encode("ascii")))
        if int(payload["exp"]) < int(datetime.now(timezone.utc).timestamp()):
            return None
        return payload
    except (KeyError, TypeError, ValueError, UnicodeDecodeError):
        return None
