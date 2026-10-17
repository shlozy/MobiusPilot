from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(subject: str, extra: dict[str, Any] | None = None) -> str:
    if not settings.jwt_secret:
        raise RuntimeError("JWT_SECRET is not configured.")
    payload = {"sub": subject, "type": "access", "iat": datetime.now(timezone.utc)}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(subject: str, extra: dict[str, Any] | None = None) -> str:
    if not settings.jwt_secret:
        raise RuntimeError("JWT_SECRET is not configured.")
    payload = {"sub": subject, "type": "refresh", "iat": datetime.now(timezone.utc)}
    if extra:
        payload.update(extra)
    expiry = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    payload["exp"] = expiry
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    if not settings.jwt_secret:
        raise RuntimeError("JWT_SECRET is not configured.")
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
