"""Password hashing and access-token helpers."""

from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_hasher.verify(password, password_hash)


def create_access_token(user_id: int, secret: str, expires_minutes: int) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": str(user_id),
            "iat": now,
            "exp": now + timedelta(minutes=expires_minutes),
        },
        secret,
        algorithm="HS256",
    )


def get_token_user_id(token: str, secret: str) -> int | None:
    try:
        claims = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            options={"require": ["exp", "sub"]},
        )
        user_id = int(claims["sub"])
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError):
        return None
    return user_id if user_id > 0 else None
