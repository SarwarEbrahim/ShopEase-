"""Admin rules. The safety rules live in small functions so they are easy to test."""

from datetime import timedelta

from sqlmodel import Session, col

from core.errors import CannotModifyAdminError, CannotModifySelfError, UserNotFoundError
from core.utils import utcnow
from features.admin import repository as admin_repository
from features.admin.schemas import (
    AdminProductList,
    AdminProductRead,
    AuditListResponse,
    AuditRead,
    CountItem,
    SecurityOverview,
    StatsResponse,
)
from features.audit import repository as audit_repository
from features.audit.models import AuditLog
from features.auth import repository as user_repository
from features.auth.models import ROLE_ADMIN, User
from features.products.models import Product
from features.products.service import ProductNotFoundError


def check_can_ban(admin: User, target: User) -> None:
    if target.id == admin.id:
        raise CannotModifySelfError()
    if target.role == ROLE_ADMIN:
        raise CannotModifyAdminError()


def check_can_change_role(admin: User, target: User) -> None:
    if target.id == admin.id:
        raise CannotModifySelfError()


def _get_target(session: Session, user_id: int) -> User:
    target = user_repository.get_by_id(session, user_id)
    if target is None:
        raise UserNotFoundError()
    return target


def list_users(session, q, role, is_banned, page, page_size):
    offset = (page - 1) * page_size
    return admin_repository.list_users(session, q, role, is_banned, offset, page_size)


def get_user(session: Session, user_id: int) -> User:
    return _get_target(session, user_id)


def ban_user(session: Session, admin: User, user_id: int, reason: str) -> User:
    target = _get_target(session, user_id)
    check_can_ban(admin, target)
    target.is_banned = True
    target.ban_reason = reason.strip()
    target.updated_at = utcnow()
    return user_repository.save(session, target)


def unban_user(session: Session, user_id: int) -> User:
    target = _get_target(session, user_id)
    target.is_banned = False
    target.ban_reason = None
    target.updated_at = utcnow()
    return user_repository.save(session, target)


def change_role(session: Session, admin: User, user_id: int, role: str) -> User:
    target = _get_target(session, user_id)
    check_can_change_role(admin, target)
    target.role = role
    target.updated_at = utcnow()
    return user_repository.save(session, target)


def bulk_ban(session: Session, admin: User, ids: list[int], reason: str) -> tuple[int, int]:
    """Ban many users. Users the rules forbid (yourself, admins) are skipped."""
    updated = skipped = 0
    for user_id in set(ids):
        target = user_repository.get_by_id(session, user_id)
        if target is None or target.id == admin.id or target.role == ROLE_ADMIN:
            skipped += 1
            continue
        target.is_banned = True
        target.ban_reason = reason.strip()
        target.updated_at = utcnow()
        user_repository.save(session, target)
        updated += 1
    return updated, skipped


def bulk_unban(session: Session, ids: list[int]) -> tuple[int, int]:
    updated = skipped = 0
    for user_id in set(ids):
        target = user_repository.get_by_id(session, user_id)
        if target is None:
            skipped += 1
            continue
        target.is_banned = False
        target.ban_reason = None
        target.updated_at = utcnow()
        user_repository.save(session, target)
        updated += 1
    return updated, skipped


def stats(session: Session) -> StatsResponse:
    now = utcnow()
    week_ago = now - timedelta(days=7)
    count = admin_repository.count
    return StatsResponse(
        total_users=count(session, User),
        banned_users=count(session, User, col(User.is_banned) == True),  # noqa: E712
        admins=count(session, User, col(User.role) == ROLE_ADMIN),
        total_products=count(session, Product),
        new_users_7d=count(session, User, col(User.created_at) >= week_ago),
        new_products_7d=count(session, Product, col(Product.created_at) >= week_ago),
        failed_logins_24h=audit_repository.count_failures_since(session, now - timedelta(days=1)),
    )


def list_audit(session: Session, event, q, page: int, page_size: int) -> AuditListResponse:
    items, total = audit_repository.list_logs(session, event, q, (page - 1) * page_size, page_size)
    return AuditListResponse(
        items=[AuditRead.model_validate(i, from_attributes=True) for i in items],
        total=total,
        page=page,
        page_size=page_size,
    )


def security_overview(session: Session) -> SecurityOverview:
    since = utcnow() - timedelta(days=1)
    by_ip = audit_repository.failures_grouped_by(session, col(AuditLog.ip_address), since)
    by_account = audit_repository.failures_grouped_by(session, col(AuditLog.username), since)
    return SecurityOverview(
        by_ip=[CountItem(key=k, count=n) for k, n in by_ip],
        by_account=[CountItem(key=k, count=n) for k, n in by_account],
    )


def _product_read(product: Product, owner_username: str | None) -> AdminProductRead:
    data = AdminProductRead.model_validate(product, from_attributes=True)
    data.owner_username = owner_username
    return data


def list_products(session: Session, q, owner_id, page: int, page_size: int) -> AdminProductList:
    rows, total = admin_repository.list_products(session, q, owner_id, (page - 1) * page_size, page_size)
    return AdminProductList(
        items=[_product_read(p, name) for p, name in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


def delete_product(session: Session, product_id: int) -> None:
    product = admin_repository.get_product(session, product_id)
    if product is None:
        raise ProductNotFoundError()
    admin_repository.delete_product(session, product)


def bulk_delete_products(session: Session, ids: list[int]) -> tuple[int, int]:
    deleted = skipped = 0
    for product_id in set(ids):
        product = admin_repository.get_product(session, product_id)
        if product is None:
            skipped += 1
            continue
        admin_repository.delete_product(session, product)
        deleted += 1
    return deleted, skipped
