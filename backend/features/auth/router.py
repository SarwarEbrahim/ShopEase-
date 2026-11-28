"""Router layer: HTTP only. Parses the request, calls the service, returns JSON."""

from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Request, Response, status
from sqlmodel import Session

from core import config
from core.database import get_session
from core.errors import AppError, WrongPasswordError
from features.audit import service as audit
from features.audit.models import (
    LOGIN,
    LOGIN_BLOCKED,
    LOGIN_FAILED,
    LOGOUT,
    PASSWORD_CHANGE,
    PASSWORD_CHANGE_FAILED,
    PROFILE_UPDATE,
    REFRESH_REUSE,
    SESSION_REVOKE,
    TOKEN_REFRESH,
)
from features.auth import service
from features.auth.dependencies import CurrentUser
from features.auth.schemas import (
    ChangePasswordRequest,
    LoginRequest,
    ProfileUpdate,
    SessionRead,
    SignupRequest,
    TokenResponse,
    UserRead,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

SessionDep = Annotated[Session, Depends(get_session)]

REFRESH_COOKIE = "refresh_token"
REFRESH_COOKIE_PATH = "/api/v1/auth"  # the browser sends it only to the auth endpoints


def _set_refresh_cookie(response: Response, token: str) -> None:
    # httpOnly: JavaScript cannot read it (protects against XSS theft).
    # SameSite=Strict: it is never sent from another site (protects against CSRF).
    response.set_cookie(
        REFRESH_COOKIE,
        token,
        max_age=config.REFRESH_TOKEN_DAYS * 24 * 3600,
        httponly=True,
        secure=config.COOKIE_SECURE,
        samesite="strict",
        path=REFRESH_COOKIE_PATH,
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(REFRESH_COOKIE, path=REFRESH_COOKIE_PATH)


@router.post("/signup", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def signup(data: SignupRequest, session: SessionDep):
    return service.signup(session, data)


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, request: Request, response: Response, session: SessionDep):
    try:
        result, refresh_token = service.login(
            session,
            data,
            ip=audit.client_ip(request),
            user_agent=(request.headers.get("user-agent") or "")[:300] or None,
        )
    except AppError as exc:
        # A wrong password counts towards the lockout; a banned or locked account does not.
        event = LOGIN_FAILED if exc.error_code == "INVALID_CREDENTIALS" else LOGIN_BLOCKED
        audit.record(session, event, request, username=data.username, detail=exc.error_code)
        raise
    _set_refresh_cookie(response, refresh_token)
    audit.record(session, LOGIN, request, user=result.user)
    return result


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    request: Request,
    response: Response,
    session: SessionDep,
    refresh_token: Annotated[str | None, Cookie()] = None,
):
    """Uses the httpOnly refresh cookie to get a new access token. The refresh token
    is replaced by a new one every time (rotation)."""
    try:
        result, new_token, user = service.refresh(session, refresh_token, audit.client_ip(request))
    except AppError as exc:
        if exc.error_code == "REFRESH_TOKEN_REUSED":
            audit.record(session, REFRESH_REUSE, request, detail=exc.error_code)
        raise
    _set_refresh_cookie(response, new_token)
    audit.record(session, TOKEN_REFRESH, request, user=user)
    return result


@router.get("/me", response_model=UserRead)
def me(user: CurrentUser):
    """A protected endpoint: it needs a valid access token."""
    return user


@router.patch("/me", response_model=UserRead)
def update_me(
    data: ProfileUpdate, request: Request, user: CurrentUser, session: SessionDep
):
    updated = service.update_profile(session, user, data)
    audit.record(session, PROFILE_UPDATE, request, user=updated)
    return updated


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    data: ChangePasswordRequest, request: Request, user: CurrentUser, session: SessionDep
) -> None:
    try:
        service.change_password(
            session,
            user,
            data.current_password,
            data.new_password,
            keep_session_id=getattr(request.state, "session_id", None),
        )
    except WrongPasswordError:
        audit.record(session, PASSWORD_CHANGE_FAILED, request, user=user)  # failed attempt
        raise
    audit.record(session, PASSWORD_CHANGE, request, user=user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    session: SessionDep,
    refresh_token: Annotated[str | None, Cookie()] = None,
) -> Response:
    """Closes this login session on the server (its refresh token stops working and
    the access token is rejected from now on) and removes the cookie."""
    user = service.logout(session, refresh_token)
    if user is not None:
        audit.record(session, LOGOUT, request, user=user)
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    _clear_refresh_cookie(response)
    return response


@router.get("/sessions", response_model=list[SessionRead])
def list_sessions(request: Request, user: CurrentUser, session: SessionDep):
    """The devices where this account is signed in (the current one is marked)."""
    return service.list_sessions(session, user, getattr(request.state, "session_id", None))


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_session(
    session_id: int, request: Request, user: CurrentUser, session: SessionDep
) -> Response:
    service.revoke_session(session, user, session_id)
    audit.record(session, SESSION_REVOKE, request, user=user, detail=f"session_id={session_id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
