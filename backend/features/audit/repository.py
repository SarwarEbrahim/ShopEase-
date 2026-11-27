"""All database queries for the activity log."""

from datetime import datetime

from sqlalchemy import func, or_
from sqlmodel import Session, col, select

from features.audit.models import LOGIN_FAILED, AuditLog


def add(session: Session, log: AuditLog) -> AuditLog:
    session.add(log)
    session.commit()
    return log


def count_recent_failures(session: Session, username: str, since: datetime) -> int:
    statement = (
        select(func.count())
        .select_from(AuditLog)
        .where(col(AuditLog.event) == LOGIN_FAILED)
        .where(col(AuditLog.username) == username)
        .where(col(AuditLog.created_at) >= since)
    )
    return session.exec(statement).one()


def _filtered(event: str | None, q: str | None):
    statement = select(AuditLog)
    if event:
        statement = statement.where(col(AuditLog.event) == event)
    if q:
        like = f"%{q.lower()}%"
        statement = statement.where(
            or_(
                func.lower(col(AuditLog.username)).like(like),
                func.lower(col(AuditLog.ip_address)).like(like),
                func.lower(col(AuditLog.detail)).like(like),
            )
        )
    return statement


def list_logs(
    session: Session, event: str | None, q: str | None, offset: int, limit: int
) -> tuple[list[AuditLog], int]:
    statement = _filtered(event, q)
    total = session.exec(select(func.count()).select_from(statement.subquery())).one()
    items = session.exec(
        statement.order_by(col(AuditLog.id).desc()).offset(offset).limit(limit)
    ).all()
    return list(items), total


def failures_grouped_by(session: Session, column, since: datetime, limit: int = 10):
    """Failed logins since `since`, grouped by a column (ip address or username)."""
    statement = (
        select(column, func.count())
        .where(col(AuditLog.event) == LOGIN_FAILED)
        .where(col(AuditLog.created_at) >= since)
        .where(column.is_not(None))
        .group_by(column)
        .order_by(func.count().desc())
        .limit(limit)
    )
    return [(row[0], row[1]) for row in session.exec(statement).all()]


def count_failures_since(session: Session, since: datetime) -> int:
    statement = (
        select(func.count())
        .select_from(AuditLog)
        .where(col(AuditLog.event) == LOGIN_FAILED)
        .where(col(AuditLog.created_at) >= since)
    )
    return session.exec(statement).one()
