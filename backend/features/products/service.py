"""Service layer: business rules, no HTTP and no SQL."""

from sqlmodel import Session

from features.auth.models import User
from features.auth.rbac import (
    PERM_RECORDS_MANAGE_ALL,
    ensure_can_access_record,
    has_permission,
)
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
    user: User,
    q: str | None,
    category: str | None,
    page: int,
    page_size: int,
) -> ProductList:
    # A normal user only sees their own products; an admin sees all of them.
    owner_id = None if has_permission(user, PERM_RECORDS_MANAGE_ALL) else user.id
    products, total = repository.list_products(
        session, q, category, page, page_size, owner_id
    )
    return ProductList(
        items=[ProductRead.model_validate(p, from_attributes=True) for p in products],
        total=total,
        page=page,
        page_size=page_size,
    )


def _load(session: Session, product_id: int) -> Product:
    product = repository.get_product(session, product_id)
    if product is None:
        raise ProductNotFoundError()
    return product


def get_product(session: Session, user: User, product_id: int) -> Product:
    product = _load(session, product_id)
    ensure_can_access_record(user, product.owner_id)  # someone else's product -> 403
    return product


def create_product(session: Session, user: User, data: ProductCreate) -> Product:
    product = Product(**data.model_dump(), owner_id=user.id)
    return repository.save_product(session, product)


def update_product(
    session: Session, user: User, product_id: int, data: ProductUpdate
) -> Product:
    product = get_product(session, user, product_id)
    for field, value in data.model_dump().items():
        setattr(product, field, value)
    product.updated_at = utcnow()
    return repository.save_product(session, product)


def delete_product(session: Session, user: User, product_id: int) -> None:
    product = get_product(session, user, product_id)
    repository.delete_product(session, product)
