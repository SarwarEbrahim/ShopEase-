"""Router layer: HTTP only. Every endpoint needs a logged-in user (CurrentUser)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from sqlmodel import Session

from core.database import get_session
from features.audit import service as audit
from features.audit.models import PRODUCT_DELETE
from features.auth.dependencies import CurrentUser
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
    user: CurrentUser,
    session: SessionDep,
    q: Annotated[str | None, Query(description="Search in the product name")] = None,
    category: Annotated[str | None, Query(description="Exact category")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 10,
):
    return service.list_products(session, user, q, category, page, page_size)


@router.get("/{product_id}", response_model=ProductRead)
def get_product(product_id: int, user: CurrentUser, session: SessionDep):
    return service.get_product(session, user, product_id)


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(data: ProductCreate, user: CurrentUser, session: SessionDep):
    return service.create_product(session, user, data)


@router.put("/{product_id}", response_model=ProductRead)
def update_product(
    product_id: int, data: ProductUpdate, user: CurrentUser, session: SessionDep
):
    return service.update_product(session, user, product_id, data)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int, request: Request, user: CurrentUser, session: SessionDep
) -> None:
    service.delete_product(session, user, product_id)
    audit.record(session, PRODUCT_DELETE, request, user=user, detail=f"product_id={product_id}")
