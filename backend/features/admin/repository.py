"""Database queries for the admin area."""

from sqlalchemy import func, or_
from sqlmodel import Session, col, select

from features.auth.models import User
from features.products.models import Product


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


def count(session: Session, model, *conditions) -> int:
    statement = select(func.count()).select_from(model)
    for condition in conditions:
        statement = statement.where(condition)
    return session.exec(statement).one()


def list_products(
    session: Session, q: str | None, owner_id: int | None, offset: int, limit: int
) -> tuple[list[tuple[Product, str | None]], int]:
    """All products with their owner's username (for moderation)."""
    statement = select(Product, User.username).join(
        User, col(User.id) == col(Product.owner_id), isouter=True
    )
    conditions = []
    if q:
        conditions.append(col(Product.name).ilike(f"%{q}%"))
    if owner_id is not None:
        conditions.append(col(Product.owner_id) == owner_id)
    for condition in conditions:
        statement = statement.where(condition)

    total = count(session, Product, *conditions)
    rows = session.exec(
        statement.order_by(col(Product.id).desc()).offset(offset).limit(limit)
    ).all()
    return [(row[0], row[1]) for row in rows], total


def get_product(session: Session, product_id: int) -> Product | None:
    return session.get(Product, product_id)


def delete_product(session: Session, product: Product) -> None:
    session.delete(product)
    session.commit()
