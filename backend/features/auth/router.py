"""Router layer: HTTP only. Parses the request, calls the service, returns JSON."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from core.database import get_session
from features.auth import service
from features.auth.dependencies import CurrentUser
from features.auth.schemas import LoginRequest, SignupRequest, TokenResponse, UserRead

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

SessionDep = Annotated[Session, Depends(get_session)]


@router.post("/signup", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def signup(data: SignupRequest, session: SessionDep):
    return service.signup(session, data)


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, session: SessionDep):
    return service.login(session, data)


@router.get("/me", response_model=UserRead)
def me(user: CurrentUser):
    """A protected endpoint: it needs a valid access token."""
    return user
