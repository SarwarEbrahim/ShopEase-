from datetime import datetime

from pydantic import BaseModel

from features.products.models import ProductBase


class ProductCreate(ProductBase):
    """Body of POST /products."""


class ProductUpdate(ProductBase):
    """Body of PUT /products/{id}. A full update: every field is sent."""


class ProductRead(ProductBase):
    """A product as returned by the API."""

    id: int
    created_at: datetime
    updated_at: datetime


class ProductList(BaseModel):
    """Paginated list returned by GET /products."""

    items: list[ProductRead]
    total: int
    page: int
    page_size: int
