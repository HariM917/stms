"""
JWT authentication service.

Handles token creation, verification, and password hashing.
Uses python-jose for JWT and passlib/bcrypt for passwords.
"""
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.config import get_settings
from app.utils.logging import get_logger

logger = get_logger("auth_service")


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False


# ---------------------------------------------------------------------------
# JWT tokens
# ---------------------------------------------------------------------------

def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a signed JWT access token with JTI (session identifier).

    Args:
        data: Payload to encode (must include 'sub'; should include 'jti').
        expires_delta: Custom expiration. Defaults to settings.jwt_expiration_hours.

    Returns:
        Encoded JWT string.
    """
    import uuid
    settings = get_settings()
    to_encode = data.copy()

    if "jti" not in to_encode:
        to_encode["jti"] = f"sess_{uuid.uuid4().hex}"

    if expires_delta is None:
        expires_delta = timedelta(hours=settings.jwt_expiration_hours)

    now = datetime.now(timezone.utc)
    to_encode.update({
        "exp": now + expires_delta,
        "iat": now,
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any] | None:
    """
    Decode and verify a JWT access token.

    Returns:
        Decoded payload dict, or None if invalid/expired.
    """
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError as e:
        logger.debug("JWT decode failed: %s", e)
        return None
