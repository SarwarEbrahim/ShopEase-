"""Admin endpoints. Every one of them needs the `admin` role (AdminUser)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from core.database import get_session
from features.admin import service
from features.admin.schemas import (
    BanRequest,
    RoleChangeRequest,
    UserDetail,
    UserListResponse,
)
from features.auth.dependencies import AdminUser
from features.auth.schemas import UserRead

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

SessionDep = Annotated[Session, Depends(get_session)]


@router.get("/users", response_model=UserListResponse)
def list_users(
    admin: AdminUser,
    session: SessionDep,
    q: str | None = Query(default=None, max_length=100, description="search username, email or name"),
    role: str | None = Query(default=None, pattern="^(user|admin)$"),
    is_banned: bool | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    items, total = service.list_users(session, q, role, is_banned, page, page_size)
    return UserListResponse(
        items=[UserRead.model_validate(u, from_attributes=True) for u in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/users/{user_id}", response_model=UserDetail)
def get_user(user_id: int, admin: AdminUser, session: SessionDep):
    return service.get_user(session, user_id)


@router.post("/users/{user_id}/ban", response_model=UserDetail)
def ban_user(user_id: int, data: BanRequest, admin: AdminUser, session: SessionDep):
    return service.ban_user(session, admin, user_id, data.reason)


@router.post("/users/{user_id}/unban", response_model=UserDetail)
def unban_user(user_id: int, admin: AdminUser, session: SessionDep):
    return service.unban_user(session, user_id)


@router.patch("/users/{user_id}/role", response_model=UserDetail)
def change_role(
    user_id: int, data: RoleChangeRequest, admin: AdminUser, session: SessionDep
):
    return service.change_role(session, admin, user_id, data.role)
