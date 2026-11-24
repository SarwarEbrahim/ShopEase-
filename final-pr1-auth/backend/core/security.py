"""Password hashing and JWT access tokens. No database and no HTTP in this file."""

import hashlib
import hmac
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from core import config

_hasher = PasswordHasher()


class TokenError(Exception):
    """Raised when a token cannot be trusted. `code` says why."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _peppered(password: str) -> str:
    # HMAC the password with the server-side pepper first. A stolen database alone
    # is then not enough to guess passwords offline.
    key = config.PASSWORD_PEPPER.encode()
    return hmac.new(key, password.encode(), hashlib.sha256).hexdigest()


def hash_password(password: str) -> str:
    return _hasher.hash(_peppered(password))


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, _peppered(password))
    except (VerifyMismatchError, InvalidHashError):
        return False


def create_access_token(user_id: int, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=config.ACCESS_TOKEN_MINUTES),
    }
    return jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Return the token payload, or raise TokenError (expired or invalid)."""
    try:
        return jwt.decode(
            token,
            config.JWT_SECRET,
            algorithms=[config.JWT_ALGORITHM],  # only this algorithm is accepted
            options={"require": ["exp", "sub"]},
        )
    except jwt.ExpiredSignatureError:
        raise TokenError("TOKEN_EXPIRED")
    except jwt.InvalidTokenError:
        raise TokenError("TOKEN_INVALID")
