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


# ---- Permissions inside a group (stored per member) ----
GROUP_CREATE = "create"  # add products to the group
GROUP_EDIT = "edit"  # change the group's products
GROUP_ASSIGN = "assign"  # assign a group product to a member
# Only the owner can rename or delete the group and manage its members.
ALL_GROUP_PERMISSIONS = frozenset({GROUP_CREATE, GROUP_EDIT, GROUP_ASSIGN})


def group_permissions(owner_id: int, user_id: int, member) -> frozenset[str]:
    """What this user may do in the group. `member` is their membership row or None."""
    if user_id == owner_id:
        return ALL_GROUP_PERMISSIONS
    if member is None:
        return frozenset()
    granted = set()
    if member.can_create:
        granted.add(GROUP_CREATE)
    if member.can_edit:
        granted.add(GROUP_EDIT)
    if member.can_assign:
        granted.add(GROUP_ASSIGN)
    return frozenset(granted)
