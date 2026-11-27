"""Router layer: HTTP only. Parses the request, calls the service, returns JSON."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from sqlmodel import Session

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
)
from features.auth import service
from features.auth.dependencies import CurrentUser
from features.auth.schemas import (
    ChangePasswordRequest,
    LoginRequest,
    ProfileUpdate,
    SignupRequest,
    TokenResponse,
    UserRead,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

SessionDep = Annotated[Session, Depends(get_session)]


@router.post("/signup", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def signup(data: SignupRequest, session: SessionDep):
    return service.signup(session, data)


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, request: Request, session: SessionDep):
    try:
        result = service.login(session, data)
    except AppError as exc:
        # A wrong password counts towards the lockout; a banned or locked account does not.
        event = LOGIN_FAILED if exc.error_code == "INVALID_CREDENTIALS" else LOGIN_BLOCKED
        audit.record(session, event, request, username=data.username, detail=exc.error_code)
        raise
    audit.record(session, LOGIN, request, user=result.user)
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
        service.change_password(session, user, data.current_password, data.new_password)
    except WrongPasswordError:
        audit.record(session, PASSWORD_CHANGE_FAILED, request, user=user)  # failed attempt
        raise
    audit.record(session, PASSWORD_CHANGE, request, user=user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, user: CurrentUser, session: SessionDep) -> Response:
    """Records the logout. The access token itself is stateless and simply expires."""
    audit.record(session, LOGOUT, request, user=user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
