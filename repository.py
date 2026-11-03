"""Repository layer: the only place that talks to the database."""

from sqlalchemy import func
from sqlmodel import Session, col, select

from features.products.models import Product


def list_products(
    session: Session,
    q: str | None,
    category: str | None,
    page: int,
    page_size: int,
) -> tuple[list[Product], int]:
    statement = select(Product)
    count_statement = select(func.count(col(Product.id)))

    if q:
        statement = statement.where(col(Product.name).ilike(f"%{q}%"))
        count_statement = count_statement.where(col(Product.name).ilike(f"%{q}%"))
    if category:
        statement = statement.where(col(Product.category) == category)
        count_statement = count_statement.where(col(Product.category) == category)

    total = session.exec(count_statement).one()
    products = session.exec(
        statement.order_by(col(Product.id).desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return list(products), total


def get_product(session: Session, product_id: int) -> Product | None:
    return session.get(Product, product_id)


def save_product(session: Session, product: Product) -> Product:
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


def delete_product(session: Session, product: Product) -> None:
    session.delete(product)
    session.commit()
