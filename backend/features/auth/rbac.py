"""The one place for RBAC: roles -> permissions, and the ownership rule.

Endpoints and services call these helpers instead of writing `if user.role == ...`
themselves. The role always comes from the database row of the current user.
"""

from core.errors import ForbiddenError
from features.auth.models import ROLE_ADMIN, ROLE_USER, User

# Permission constants
PERM_RECORDS_MANAGE_ALL = "records:manage_all"  # read, change, delete anyone's records
PERM_USERS_MANAGE = "users:manage"  # ban, unban, change roles
PERM_AUDIT_VIEW = "audit:view"  # activity log, security view, exports

ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    ROLE_USER: frozenset(),  # a normal user only works with their own records
    ROLE_ADMIN: frozenset({PERM_RECORDS_MANAGE_ALL, PERM_USERS_MANAGE, PERM_AUDIT_VIEW}),
}


def has_permission(user: User, permission: str) -> bool:
    return permission in ROLE_PERMISSIONS.get(user.role, frozenset())


def can_access_record(user: User, owner_id: int | None) -> bool:
    """Ownership rule: the owner, or someone allowed to manage all records."""
    return owner_id == user.id or has_permission(user, PERM_RECORDS_MANAGE_ALL)


def ensure_can_access_record(user: User, owner_id: int | None) -> None:
    if not can_access_record(user, owner_id):
        raise ForbiddenError()
