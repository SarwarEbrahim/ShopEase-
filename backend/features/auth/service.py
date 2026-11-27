"""Business rules for signup, login, profile and password. No HTTP and no SQL here."""

from datetime import timedelta

from sqlmodel import Session

from core import config, security
from core.errors import (
    EmailTakenError,
    InvalidCredentialsError,
    PasswordUnchangedError,
    TooManyAttemptsError,
    UserBannedError,
    UsernameTakenError,
    WrongPasswordError,
)
from core.utils import utcnow
from features.audit import repository as audit_repository
from features.auth import repository
from features.auth.models import ROLE_USER, User
from features.auth.schemas import (
    LoginRequest,
    ProfileUpdate,
    SignupRequest,
    TokenResponse,
    UserRead,
)

# Brute-force protection: after 5 failed logins for one username in 15 minutes,
# further attempts are refused (even with the right password) until the window passes.
MAX_FAILED_LOGINS = 5
LOCKOUT_WINDOW = timedelta(minutes=15)

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
    username = data.username.lower()
    failures = audit_repository.count_recent_failures(
        session, username, utcnow() - LOCKOUT_WINDOW
    )
    if failures >= MAX_FAILED_LOGINS:
        raise TooManyAttemptsError()

    user = repository.get_by_username(session, username)
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


def update_profile(session: Session, user: User, data: ProfileUpdate) -> User:
    if data.email is not None:
        email = data.email.lower()
        if email != user.email:
            if repository.get_by_email(session, email):
                raise EmailTakenError()
            user.email = email
    if data.full_name is not None:
        user.full_name = data.full_name.strip()
    user.updated_at = utcnow()
    return repository.save(session, user)


def change_password(
    session: Session, user: User, current_password: str, new_password: str
) -> None:
    # The current password is required, so a stolen token alone cannot change it.
    if not security.verify_password(current_password, user.password_hash):
        raise WrongPasswordError()
    if security.verify_password(new_password, user.password_hash):
        raise PasswordUnchangedError()
    user.password_hash = security.hash_password(new_password)
    user.updated_at = utcnow()
    repository.save(session, user)
