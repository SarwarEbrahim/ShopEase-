"""Router layer: HTTP only. Parses the request, calls the service, returns JSON."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlmodel import Session

from core.database import get_session
from features.products import service
from features.products.schemas import (
    ProductCreate,
    ProductList,
    ProductRead,
    ProductUpdate,
)

router = APIRouter(prefix="/api/v1/products", tags=["products"])

SessionDep = Annotated[Session, Depends(get_session)]


@router.get("", response_model=ProductList)
def list_products(
    session: SessionDep,
    q: Annotated[str | None, Query(description="Search in the product name")] = None,
    category: Annotated[str | None, Query(description="Exact category")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 10,
):
    return service.list_products(session, q, category, page, page_size)


@router.get("/{product_id}", response_model=ProductRead)
def get_product(product_id: int, session: SessionDep):
    return service.get_product(session, product_id)


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(data: ProductCreate, session: SessionDep):
    return service.create_product(session, data)


@router.put("/{product_id}", response_model=ProductRead)
def update_product(product_id: int, data: ProductUpdate, session: SessionDep):
    return service.update_product(session, product_id, data)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, session: SessionDep) -> None:
    service.delete_product(session, product_id)
