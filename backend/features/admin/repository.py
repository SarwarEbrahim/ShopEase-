"""Database queries for the admin area."""

from sqlalchemy import func, or_
from sqlmodel import Session, select

from features.auth.models import User


def list_users(
    session: Session,
    q: str | None,
    role: str | None,
    is_banned: bool | None,
    offset: int,
    limit: int,
) -> tuple[list[User], int]:
    query = select(User)
    if q:
        like = f"%{q.lower()}%"
        query = query.where(
            or_(
                func.lower(User.username).like(like),
                func.lower(User.email).like(like),
                func.lower(User.full_name).like(like),
            )
        )
    if role:
        query = query.where(User.role == role)
    if is_banned is not None:
        query = query.where(User.is_banned == is_banned)

    total = session.exec(select(func.count()).select_from(query.subquery())).one()
    items = session.exec(query.order_by(User.id).offset(offset).limit(limit)).all()
    return list(items), total
