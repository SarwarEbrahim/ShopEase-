"""Group endpoints. Every one needs a logged-in user; the service checks the
group permissions."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from sqlmodel import Session

from core.database import get_session
from features.audit import service as audit
from features.audit.models import GROUP_DELETE, PRODUCT_DELETE
from features.auth.dependencies import CurrentUser
from features.groups import service
from features.groups.schemas import (
    AssignRequest,
    GroupDetail,
    GroupName,
    GroupProductRead,
    GroupRead,
    MemberAdd,
    MemberRead,
    MemberUpdate,
)
from features.products.schemas import ProductCreate, ProductUpdate

router = APIRouter(prefix="/api/v1/groups", tags=["groups"])

SessionDep = Annotated[Session, Depends(get_session)]


@router.get("", response_model=list[GroupRead])
def list_groups(user: CurrentUser, session: SessionDep):
    return service.list_my_groups(session, user)


@router.post("", response_model=GroupRead, status_code=status.HTTP_201_CREATED)
def create_group(data: GroupName, user: CurrentUser, session: SessionDep):
    return service.create_group(session, user, data.name)


@router.get("/{group_id}", response_model=GroupDetail)
def get_group(group_id: int, user: CurrentUser, session: SessionDep):
    return service.get_group_detail(session, user, group_id)


@router.patch("/{group_id}", response_model=GroupRead)
def rename_group(group_id: int, data: GroupName, user: CurrentUser, session: SessionDep):
    return service.rename_group(session, user, group_id, data.name)


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(group_id: int, request: Request, user: CurrentUser, session: SessionDep) -> Response:
    service.delete_group(session, user, group_id)
    audit.record(session, GROUP_DELETE, request, user=user, detail=f"group_id={group_id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ------------------------------------------------------------------ members


@router.post("/{group_id}/members", response_model=MemberRead, status_code=status.HTTP_201_CREATED)
def add_member(group_id: int, data: MemberAdd, user: CurrentUser, session: SessionDep):
    return service.add_member(session, user, group_id, data)


@router.patch("/{group_id}/members/{member_user_id}", response_model=MemberRead)
def update_member(
    group_id: int, member_user_id: int, data: MemberUpdate, user: CurrentUser, session: SessionDep
):
    return service.update_member(session, user, group_id, member_user_id, data)


@router.delete("/{group_id}/members/{member_user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(group_id: int, member_user_id: int, user: CurrentUser, session: SessionDep) -> Response:
    service.remove_member(session, user, group_id, member_user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ----------------------------------------------------------------- products


@router.get("/{group_id}/products", response_model=list[GroupProductRead])
def list_products(group_id: int, user: CurrentUser, session: SessionDep):
    return service.list_products(session, user, group_id)


@router.post("/{group_id}/products", response_model=GroupProductRead, status_code=status.HTTP_201_CREATED)
def create_product(group_id: int, data: ProductCreate, user: CurrentUser, session: SessionDep):
    return service.create_product(session, user, group_id, data)


@router.put("/{group_id}/products/{product_id}", response_model=GroupProductRead)
def update_product(
    group_id: int, product_id: int, data: ProductUpdate, user: CurrentUser, session: SessionDep
):
    return service.update_product(session, user, group_id, product_id, data)


@router.delete("/{group_id}/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    group_id: int, product_id: int, request: Request, user: CurrentUser, session: SessionDep
) -> Response:
    service.delete_product(session, user, group_id, product_id)
    audit.record(session, PRODUCT_DELETE, request, user=user, detail=f"group_id={group_id} product_id={product_id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{group_id}/products/{product_id}/assign", response_model=GroupProductRead)
def assign_product(
    group_id: int, product_id: int, data: AssignRequest, user: CurrentUser, session: SessionDep
):
    return service.assign_product(session, user, group_id, product_id, data.user_id)
