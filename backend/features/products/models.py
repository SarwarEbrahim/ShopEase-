from datetime import datetime, timezone
from decimal import Decimal

from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ProductBase(SQLModel):
    """Fields shared by the table and the request/response schemas.

    The validation rules here follow the SRS (section 3.5).
    """

    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    stock: int = Field(ge=0)
    category: str = Field(min_length=1, max_length=60, index=True)


class Product(ProductBase, table=True):
    """The `products` table (TDD, Data Model, MVP)."""

    __tablename__ = "products"

    id: int | None = Field(default=None, primary_key=True)
    # The user who owns this product (users.id). Used by the ownership rules.
    owner_id: int | None = Field(default=None, index=True)
    # Set when the product belongs to a group (shared with the members), and who
    # it is assigned to inside that group.
    group_id: int | None = Field(default=None, index=True)
    assignee_id: int | None = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
