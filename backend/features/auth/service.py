"""Business rules for signup, login, profile and password. No HTTP and no SQL here."""

from datetime import timedelta

from sqlmodel import Session

from core import config, security
from core.errors import (
    EmailTakenError,
    InvalidCredentialsError,
    PasswordUnchangedError,
    RefreshTokenInvalidError,
    RefreshTokenReusedError,
    SessionNotFoundError,
    TooManyAttemptsError,
    UserBannedError,
    UsernameTakenError,
    WrongPasswordError,
)
from core.utils import as_utc, utcnow
from features.audit import repository as audit_repository
from features.auth import repository, session_repository
from features.auth.models import ROLE_USER, User, UserSession
from features.auth.schemas import (
    LoginRequest,
    ProfileUpdate,
    SessionRead,
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


def _token_response(user: User, session_id: int) -> TokenResponse:
    return TokenResponse(
        access_token=security.create_access_token(user.id, user.role, session_id),
        expires_in=config.ACCESS_TOKEN_MINUTES * 60,
        user=UserRead.model_validate(user, from_attributes=True),
    )


def login(
    session: Session, data: LoginRequest, ip: str | None = None, user_agent: str | None = None
) -> tuple[TokenResponse, str]:
    """Check the password and open a session. Returns the access token response and
    the refresh token (the router puts the refresh token in an httpOnly cookie)."""
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

    refresh_token = security.generate_refresh_token()
    now = utcnow()
    row = session_repository.save(
        session,
        UserSession(
            user_id=user.id,
            token_hash=security.hash_refresh_token(refresh_token),
            ip_address=ip,
            user_agent=user_agent,
            created_at=now,
            last_used_at=now,
            expires_at=now + timedelta(days=config.REFRESH_TOKEN_DAYS),
        ),
    )
    return _token_response(user, row.id), refresh_token


def refresh(
    session: Session, token: str | None, ip: str | None = None
) -> tuple[TokenResponse, str, User]:
    """Swap a valid refresh token for a new access token AND a new refresh token
    (rotation). Using an old refresh token again closes the whole session."""
    if not token:
        raise RefreshTokenInvalidError()
    token_hash = security.hash_refresh_token(token)
    row = session_repository.get_by_token_hash(session, token_hash)

    if row is None:
        # Not the current token. If it is the PREVIOUS token of a session, someone is
        # replaying an old token (it may have been stolen): close that session.
        old = session_repository.get_by_previous_hash(session, token_hash)
        if old is not None and old.revoked_at is None:
            old.revoked_at = utcnow()
            old.revoked_reason = "reuse_detected"
            session_repository.save(session, old)
            raise RefreshTokenReusedError()
        raise RefreshTokenInvalidError()

    now = utcnow()
    if row.revoked_at is not None or as_utc(row.expires_at) <= now:
        raise RefreshTokenInvalidError()
    user = repository.get_by_id(session, row.user_id)
    if user is None:
        raise RefreshTokenInvalidError()
    if user.is_banned:
        row.revoked_at = now
        row.revoked_reason = "banned"
        session_repository.save(session, row)
        raise UserBannedError()

    new_token = security.generate_refresh_token()
    row.previous_hash = row.token_hash
    row.token_hash = security.hash_refresh_token(new_token)
    row.last_used_at = now
    row.expires_at = now + timedelta(days=config.REFRESH_TOKEN_DAYS)
    if ip:
        row.ip_address = ip
    session_repository.save(session, row)
    return _token_response(user, row.id), new_token, user


def logout(session: Session, token: str | None) -> User | None:
    """Close the session that owns this refresh token. Returns its user (for the log)."""
    if not token:
        return None
    row = session_repository.get_by_token_hash(session, security.hash_refresh_token(token))
    if row is None:
        return None
    if row.revoked_at is None:
        row.revoked_at = utcnow()
        row.revoked_reason = "logout"
        session_repository.save(session, row)
    return repository.get_by_id(session, row.user_id)


def list_sessions(session: Session, user: User, current_id: int | None) -> list[SessionRead]:
    rows = session_repository.list_active(session, user.id, utcnow())
    return [
        SessionRead(
            id=r.id,
            ip_address=r.ip_address,
            user_agent=r.user_agent,
            created_at=r.created_at,
            last_used_at=r.last_used_at,
            expires_at=r.expires_at,
            current=r.id == current_id,
        )
        for r in rows
    ]


def revoke_session(session: Session, user: User, session_id: int) -> None:
    """A user can only revoke their own sessions (anything else is 404)."""
    row = session_repository.get(session, session_id)
    if row is None or row.user_id != user.id:
        raise SessionNotFoundError()
    if row.revoked_at is None:
        row.revoked_at = utcnow()
        row.revoked_reason = "revoked_by_user"
        session_repository.save(session, row)


def revoke_all_sessions(
    session: Session, user_id: int, reason: str, except_id: int | None = None
) -> int:
    return session_repository.revoke_all(session, user_id, utcnow(), reason, except_id)


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
    session: Session,
    user: User,
    current_password: str,
    new_password: str,
    keep_session_id: int | None = None,
) -> None:
    # The current password is required, so a stolen token alone cannot change it.
    if not security.verify_password(current_password, user.password_hash):
        raise WrongPasswordError()
    if security.verify_password(new_password, user.password_hash):
        raise PasswordUnchangedError()
    user.password_hash = security.hash_password(new_password)
    user.updated_at = utcnow()
    repository.save(session, user)
    # Every other device is signed out; the one that changed the password stays.
    revoke_all_sessions(session, user.id, "password_change", except_id=keep_session_id)
