"""Admin rules. The safety rules live in small functions so they are easy to test."""

from sqlmodel import Session

from core.errors import CannotModifyAdminError, CannotModifySelfError, UserNotFoundError
from core.utils import utcnow
from features.admin import repository as admin_repository
from features.auth import repository as user_repository
from features.auth.models import ROLE_ADMIN, User


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
