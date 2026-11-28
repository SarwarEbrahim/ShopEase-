"""All database queries for login sessions (refresh tokens)."""

from datetime import datetime

from sqlmodel import Session, col, select

from features.auth.models import UserSession


def get(session: Session, session_id: int) -> UserSession | None:
    return session.get(UserSession, session_id)


def get_by_token_hash(session: Session, token_hash: str) -> UserSession | None:
    return session.exec(
        select(UserSession).where(col(UserSession.token_hash) == token_hash)
    ).first()


def get_by_previous_hash(session: Session, token_hash: str) -> UserSession | None:
    return session.exec(
        select(UserSession).where(col(UserSession.previous_hash) == token_hash)
    ).first()


def save(session: Session, row: UserSession) -> UserSession:
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def list_active(session: Session, user_id: int, now: datetime) -> list[UserSession]:
    statement = (
        select(UserSession)
        .where(col(UserSession.user_id) == user_id)
        .where(col(UserSession.revoked_at).is_(None))
        .where(col(UserSession.expires_at) > now)
        .order_by(col(UserSession.last_used_at).desc())
    )
    return list(session.exec(statement).all())


def revoke_all(
    session: Session, user_id: int, now: datetime, reason: str, except_id: int | None = None
) -> int:
    """Revoke every open session of a user (optionally keeping one). Returns how many."""
    rows = session.exec(
        select(UserSession)
        .where(col(UserSession.user_id) == user_id)
        .where(col(UserSession.revoked_at).is_(None))
    ).all()
    count = 0
    for row in rows:
        if except_id is not None and row.id == except_id:
            continue
        row.revoked_at = now
        row.revoked_reason = reason
        session.add(row)
        count += 1
    session.commit()
    return count
