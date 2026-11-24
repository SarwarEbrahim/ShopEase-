"""Business rules for signup and login. No HTTP and no SQL here."""

from sqlmodel import Session

from core import config, security
from core.errors import (
    EmailTakenError,
    InvalidCredentialsError,
    UserBannedError,
    UsernameTakenError,
)
from features.auth import repository
from features.auth.models import ROLE_USER, User
from features.auth.schemas import LoginRequest, SignupRequest, TokenResponse, UserRead

# Used when the username does not exist, so a wrong username and a wrong password
# take about the same time (the response does not reveal which one was wrong).
_DUMMY_HASH = security.hash_password("not-a-real-password-1")


def signup(session: Session, data: SignupRequest) -> User:
    username = data.username.lower()
    email = data.email.lower()
    if repository.get_by_username(session, username):
        raise UsernameTakenError()
    if repository.get_by_email(session, email):
        raise EmailTakenError()
    user = User(
        username=username,
        email=email,
        full_name=data.full_name.strip(),
        password_hash=security.hash_password(data.password),
        role=ROLE_USER,  # nobody can choose their own role at signup
    )
    return repository.save(session, user)


def login(session: Session, data: LoginRequest) -> TokenResponse:
    user = repository.get_by_username(session, data.username.lower())
    password_ok = security.verify_password(
        data.password, user.password_hash if user else _DUMMY_HASH
    )
    if user is None or not password_ok:
        raise InvalidCredentialsError()
    if user.is_banned:
        raise UserBannedError()
    return TokenResponse(
        access_token=security.create_access_token(user.id, user.role),
        expires_in=config.ACCESS_TOKEN_MINUTES * 60,
        user=UserRead.model_validate(user, from_attributes=True),
    )
