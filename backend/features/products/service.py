"""Service layer: business rules, no HTTP and no SQL."""

from sqlmodel import Session

from features.products import repository
from features.products.models import Product, utcnow
from features.products.schemas import (
    ProductCreate,
    ProductList,
    ProductRead,
    ProductUpdate,
)


class ProductNotFoundError(Exception):
    """Raised when a product id does not exist (handled as HTTP 404)."""


def list_products(
    session: Session,
    q: str | None,
    category: str | None,
    page: int,
    page_size: int,
) -> ProductList:
    products, total = repository.list_products(session, q, category, page, page_size)
    return ProductList(
        items=[ProductRead.model_validate(p, from_attributes=True) for p in products],
        total=total,
        page=page,
        page_size=page_size,
    )


def get_product(session: Session, product_id: int) -> Product:
    product = repository.get_product(session, product_id)
    if product is None:
        raise ProductNotFoundError()
    return product


def create_product(session: Session, data: ProductCreate) -> Product:
    product = Product(**data.model_dump())
    return repository.save_product(session, product)


def update_product(session: Session, product_id: int, data: ProductUpdate) -> Product:
    product = get_product(session, product_id)
    for field, value in data.model_dump().items():
        setattr(product, field, value)
    product.updated_at = utcnow()
    return repository.save_product(session, product)


def delete_product(session: Session, product_id: int) -> None:
    product = get_product(session, product_id)
    repository.delete_product(session, product)
