"""`CurrentUser`: the dependency that protects an endpoint.

Add `user: CurrentUser` to an endpoint and FastAPI runs get_current_user first.
It reads the Bearer token, verifies it and loads the user. Any problem is a 401.
"""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from core import security
from core.database import get_session
from core.errors import (
    ForbiddenError,
    NotAuthenticatedError,
    TokenExpiredError,
    TokenInvalidError,
    UserBannedError,
)
from features.auth import repository
from features.auth.models import ROLE_ADMIN, User

# auto_error=False: we raise our own 401 with the SRS error body.
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: Annotated[Session, Depends(get_session)],
) -> User:
    if credentials is None:
        raise NotAuthenticatedError()

    try:
        payload = security.decode_access_token(credentials.credentials)
    except security.TokenError as exc:
        if exc.code == "TOKEN_EXPIRED":
            raise TokenExpiredError()
        raise TokenInvalidError()

    try:
        user_id = int(payload["sub"])
    except (KeyError, ValueError):
        raise TokenInvalidError()

    user = repository.get_by_id(session, user_id)
    if user is None:
        raise NotAuthenticatedError()
    if user.is_banned:
        # A banned user is rejected on the very next request, even with a valid token.
        raise UserBannedError()
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*allowed_roles: str):
    """RBAC: build a dependency that only lets users with one of these roles in.

    It runs get_current_user first (so 401 / banned checks still apply), then
    compares the role stored in the database. Wrong role -> 403.
    """

    def checker(user: CurrentUser) -> User:
        if user.role not in allowed_roles:
            raise ForbiddenError()
        return user

    return checker


# Use `admin: AdminUser` in an endpoint to make it admin-only.
AdminUser = Annotated[User, Depends(require_roles(ROLE_ADMIN))]
