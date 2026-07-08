from datetime import datetime, timedelta, timezone
from typing import Literal

import jwt
from passlib.context import CryptContext

from app.config import get_settings

settings = get_settings()

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def _create_token(subject: str, expires_delta: timedelta, token_type: Literal["access", "refresh"]) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": subject, "type": token_type, "iat": now, "exp": now + expires_delta}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: int) -> str:
    return _create_token(
        str(user_id), timedelta(minutes=settings.access_token_expire_minutes), "access"
    )


def create_refresh_token(user_id: int) -> str:
    return _create_token(str(user_id), timedelta(days=settings.refresh_token_expire_days), "refresh")


class TokenError(Exception):
    pass


def decode_token(token: str, expected_type: Literal["access", "refresh"]) -> int:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise TokenError("유효하지 않은 토큰입니다.") from exc

    if payload.get("type") != expected_type:
        raise TokenError("토큰 종류가 올바르지 않습니다.")

    try:
        return int(payload["sub"])
    except (KeyError, ValueError, TypeError) as exc:
        raise TokenError("토큰 내용이 올바르지 않습니다.") from exc
