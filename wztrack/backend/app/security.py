from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


def create_access_token(payload: dict[str, Any]) -> str:
    data = payload.copy()
    data["exp"] = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    data["type"] = "access"
    return jwt.encode(data, settings.jwt_private_key_pem, algorithm=settings.jwt_algorithm)


def create_refresh_token(payload: dict[str, Any]) -> str:
    data = payload.copy()
    data["exp"] = datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expire_days
    )
    data["type"] = "refresh"
    return jwt.encode(data, settings.jwt_private_key_pem, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    """Raises JWTError on any failure."""
    return jwt.decode(token, settings.jwt_public_key_pem, algorithms=[settings.jwt_algorithm])


def hash_token(token: str) -> str:
    """SHA-256 hex digest used to store refresh tokens."""
    import hashlib
    return hashlib.sha256(token.encode()).hexdigest()


__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "hash_token",
]
