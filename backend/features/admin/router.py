"""Admin endpoints. Every one of them needs the `admin` role (AdminUser)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlmodel import Session

from core.database import get_session
from features.admin import service
from features.admin.exports import to_csv
from features.admin.schemas import (
    AdminGroupList,
    AdminProductList,
    AuditListResponse,
    BanRequest,
    BulkBanRequest,
    BulkResult,
    IdsRequest,
    RoleChangeRequest,
    SecurityOverview,
    StatsResponse,
    UserDetail,
    UserListResponse,
    UserOverview,
)
from features.audit import service as audit
from features.audit.models import (
    BAN,
    EXPORT,
    GROUP_DELETE,
    PRODUCT_DELETE,
    ROLE_CHANGE,
    SESSION_REVOKE,
    UNBAN,
)
from features.auth.dependencies import AdminUser
from features.auth.schemas import UserRead

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

SessionDep = Annotated[Session, Depends(get_session)]

ROLE_PATTERN = "^(user|admin)$"
EXPORT_LIMIT = 10000


def _csv_response(text: str, filename: str) -> Response:
    return Response(
        content=text,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------- statistics


@router.get("/stats", response_model=StatsResponse)
def stats(admin: AdminUser, session: SessionDep):
    return service.stats(session)


# --------------------------------------------------------------------- users


@router.get("/users", response_model=UserListResponse)
def list_users(
    admin: AdminUser,
    session: SessionDep,
    q: str | None = Query(default=None, max_length=100, description="search username, email or name"),
    role: str | None = Query(default=None, pattern=ROLE_PATTERN),
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


@router.post("/users/bulk-ban", response_model=BulkResult)
def bulk_ban(
    data: BulkBanRequest, request: Request, admin: AdminUser, session: SessionDep
):
    updated, skipped = service.bulk_ban(session, admin, data.ids, data.reason)
    audit.record(session, BAN, request, user=admin, detail=f"bulk ids={data.ids} reason={data.reason}")
    return BulkResult(updated=updated, skipped=skipped)


@router.post("/users/bulk-unban", response_model=BulkResult)
def bulk_unban(data: IdsRequest, request: Request, admin: AdminUser, session: SessionDep):
    updated, skipped = service.bulk_unban(session, data.ids)
    audit.record(session, UNBAN, request, user=admin, detail=f"bulk ids={data.ids}")
    return BulkResult(updated=updated, skipped=skipped)


@router.get("/users/{user_id}", response_model=UserDetail)
def get_user(user_id: int, admin: AdminUser, session: SessionDep):
    return service.get_user(session, user_id)


@router.get("/users/{user_id}/overview", response_model=UserOverview)
def user_overview(user_id: int, admin: AdminUser, session: SessionDep):
    """User detail: profile, open sessions, latest activity, record counts."""
    return service.user_overview(session, user_id)


@router.post("/users/{user_id}/revoke-sessions", response_model=BulkResult)
def revoke_user_sessions(
    user_id: int, request: Request, admin: AdminUser, session: SessionDep
):
    count = service.revoke_user_sessions(session, user_id)
    audit.record(session, SESSION_REVOKE, request, user=admin, detail=f"target_id={user_id} count={count}")
    return BulkResult(updated=count, skipped=0)


@router.post("/users/{user_id}/ban", response_model=UserDetail)
def ban_user(
    user_id: int, data: BanRequest, request: Request, admin: AdminUser, session: SessionDep
):
    target = service.ban_user(session, admin, user_id, data.reason)
    audit.record(session, BAN, request, user=admin, detail=f"target={target.username} reason={data.reason}")
    return target


@router.post("/users/{user_id}/unban", response_model=UserDetail)
def unban_user(user_id: int, request: Request, admin: AdminUser, session: SessionDep):
    target = service.unban_user(session, user_id)
    audit.record(session, UNBAN, request, user=admin, detail=f"target={target.username}")
    return target


@router.patch("/users/{user_id}/role", response_model=UserDetail)
def change_role(
    user_id: int,
    data: RoleChangeRequest,
    request: Request,
    admin: AdminUser,
    session: SessionDep,
):
    target = service.change_role(session, admin, user_id, data.role)
    audit.record(session, ROLE_CHANGE, request, user=admin, detail=f"target={target.username} role={data.role}")
    return target


# ------------------------------------------------------------------ products


@router.get("/products", response_model=AdminProductList)
def list_products(
    admin: AdminUser,
    session: SessionDep,
    q: str | None = Query(default=None, max_length=100),
    owner_id: int | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    return service.list_products(session, q, owner_id, page, page_size)


@router.post("/products/bulk-delete", response_model=BulkResult)
def bulk_delete_products(
    data: IdsRequest, request: Request, admin: AdminUser, session: SessionDep
):
    deleted, skipped = service.bulk_delete_products(session, data.ids)
    audit.record(session, PRODUCT_DELETE, request, user=admin, detail=f"bulk ids={data.ids}")
    return BulkResult(updated=deleted, skipped=skipped)


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int, request: Request, admin: AdminUser, session: SessionDep
) -> Response:
    service.delete_product(session, product_id)
    audit.record(session, PRODUCT_DELETE, request, user=admin, detail=f"product_id={product_id} (admin)")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# -------------------------------------------------------------------- groups


@router.get("/groups", response_model=AdminGroupList)
def list_groups(
    admin: AdminUser,
    session: SessionDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    return service.list_groups(session, page, page_size)


@router.delete("/groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(group_id: int, request: Request, admin: AdminUser, session: SessionDep) -> Response:
    service.delete_group(session, group_id)
    audit.record(session, GROUP_DELETE, request, user=admin, detail=f"group_id={group_id} (admin)")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ------------------------------------------------------- activity and security


@router.get("/audit", response_model=AuditListResponse)
def list_audit(
    admin: AdminUser,
    session: SessionDep,
    event: str | None = Query(default=None, max_length=40),
    q: str | None = Query(default=None, max_length=100, description="search username, IP or detail"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    return service.list_audit(session, event, q, page, page_size)


@router.get("/security", response_model=SecurityOverview)
def security(admin: AdminUser, session: SessionDep):
    return service.security_overview(session)


# ------------------------------------------------------------------- exports
# Each export follows the same filters as the matching list above.


@router.get("/export/users.csv")
def export_users(
    request: Request,
    admin: AdminUser,
    session: SessionDep,
    q: str | None = Query(default=None, max_length=100),
    role: str | None = Query(default=None, pattern=ROLE_PATTERN),
    is_banned: bool | None = None,
):
    users, _ = service.list_users(session, q, role, is_banned, 1, EXPORT_LIMIT)
    text = to_csv(
        ["id", "username", "email", "full_name", "role", "is_banned", "created_at"],
        [[u.id, u.username, u.email, u.full_name, u.role, u.is_banned, u.created_at] for u in users],
    )
    audit.record(session, EXPORT, request, user=admin, detail="users.csv")
    return _csv_response(text, "users.csv")


@router.get("/export/products.csv")
def export_products(
    request: Request,
    admin: AdminUser,
    session: SessionDep,
    q: str | None = Query(default=None, max_length=100),
    owner_id: int | None = None,
):
    result = service.list_products(session, q, owner_id, 1, EXPORT_LIMIT)
    text = to_csv(
        ["id", "name", "category", "price", "stock", "owner_id", "owner_username", "created_at"],
        [
            [p.id, p.name, p.category, p.price, p.stock, p.owner_id, p.owner_username, p.created_at]
            for p in result.items
        ],
    )
    audit.record(session, EXPORT, request, user=admin, detail="products.csv")
    return _csv_response(text, "products.csv")


@router.get("/export/audit.csv")
def export_audit(
    request: Request,
    admin: AdminUser,
    session: SessionDep,
    event: str | None = Query(default=None, max_length=40),
    q: str | None = Query(default=None, max_length=100),
):
    result = service.list_audit(session, event, q, 1, EXPORT_LIMIT)
    text = to_csv(
        ["id", "event", "user_id", "username", "ip_address", "user_agent", "detail", "created_at"],
        [
            [l.id, l.event, l.user_id, l.username, l.ip_address, l.user_agent, l.detail, l.created_at]
            for l in result.items
        ],
    )
    audit.record(session, EXPORT, request, user=admin, detail="audit.csv")
    return _csv_response(text, "audit.csv")
