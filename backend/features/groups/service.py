"""Group rules: who may see a group, and what each member may do in it.

Owner  -> everything (rename, delete, manage members, create/edit/assign products)
Member -> only the permissions the owner gave: create, edit, assign
Others -> 403 (an admin can look at a group and delete it from the admin area)
"""

from sqlmodel import Session

from core.errors import (
    AlreadyMemberError,
    ForbiddenError,
    GroupNotFoundError,
    GroupPermissionError,
    NotAMemberError,
    NotGroupOwnerError,
    UserNotFoundError,
)
from core.utils import utcnow
from features.auth import repository as user_repository
from features.auth.models import User
from features.auth.rbac import (
    GROUP_ASSIGN,
    GROUP_CREATE,
    GROUP_EDIT,
    PERM_RECORDS_MANAGE_ALL,
    group_permissions,
    has_permission,
)
from features.groups import repository
from features.groups.models import Group, GroupMember
from features.groups.schemas import (
    GroupDetail,
    GroupProductRead,
    GroupRead,
    MemberAdd,
    MemberRead,
    MemberUpdate,
)
from features.products.models import Product
from features.products.schemas import ProductCreate, ProductUpdate


# ---------------------------------------------------------------- helpers


def _get_group(session: Session, group_id: int) -> Group:
    group = repository.get_group(session, group_id)
    if group is None:
        raise GroupNotFoundError()
    return group


def _my_permissions(session: Session, group: Group, user: User) -> frozenset[str]:
    member = None if group.owner_id == user.id else repository.get_member(session, group.id, user.id)
    return group_permissions(group.owner_id, user.id, member)


def _is_involved(session: Session, group: Group, user: User) -> bool:
    """Owner, member or admin: allowed to look at the group."""
    if group.owner_id == user.id or has_permission(user, PERM_RECORDS_MANAGE_ALL):
        return True
    return repository.get_member(session, group.id, user.id) is not None


def _ensure_can_view(session: Session, group: Group, user: User) -> None:
    if not _is_involved(session, group, user):
        raise ForbiddenError()


def _ensure_owner(group: Group, user: User) -> None:
    if group.owner_id != user.id:
        raise NotGroupOwnerError()


def _ensure_permission(session: Session, group: Group, user: User, permission: str) -> None:
    if permission not in _my_permissions(session, group, user):
        raise GroupPermissionError()


def _group_read(session: Session, group: Group, user: User) -> GroupRead:
    owner = user_repository.get_by_id(session, group.owner_id)
    return GroupRead(
        id=group.id,
        name=group.name,
        owner_id=group.owner_id,
        owner_username=owner.username if owner else None,
        is_owner=group.owner_id == user.id,
        my_permissions=sorted(_my_permissions(session, group, user)),
        created_at=group.created_at,
    )


def _member_read(member: GroupMember, user: User) -> MemberRead:
    return MemberRead(
        user_id=user.id,
        username=user.username,
        full_name=user.full_name,
        can_create=member.can_create,
        can_edit=member.can_edit,
        can_assign=member.can_assign,
    )


def _product_read(product: Product, assignee_username: str | None) -> GroupProductRead:
    data = GroupProductRead.model_validate(product, from_attributes=True)
    data.assignee_username = assignee_username
    return data


def _get_product(session: Session, group: Group, product_id: int) -> Product:
    from features.products.service import ProductNotFoundError

    product = repository.get_group_product(session, group.id, product_id)
    if product is None:
        raise ProductNotFoundError()
    return product


# ----------------------------------------------------------------- groups


def list_my_groups(session: Session, user: User) -> list[GroupRead]:
    return [_group_read(session, g, user) for g in repository.groups_for_user(session, user.id)]


def create_group(session: Session, user: User, name: str) -> GroupRead:
    group = repository.save(session, Group(name=name.strip(), owner_id=user.id))
    return _group_read(session, group, user)


def get_group_detail(session: Session, user: User, group_id: int) -> GroupDetail:
    group = _get_group(session, group_id)
    _ensure_can_view(session, group, user)
    members = [_member_read(m, u) for m, u in repository.list_members(session, group.id)]
    base = _group_read(session, group, user)
    return GroupDetail(**base.model_dump(), members=members)


def rename_group(session: Session, user: User, group_id: int, name: str) -> GroupRead:
    group = _get_group(session, group_id)
    _ensure_owner(group, user)
    group.name = name.strip()
    group.updated_at = utcnow()
    return _group_read(session, repository.save(session, group), user)


def delete_group(session: Session, user: User, group_id: int) -> None:
    group = _get_group(session, group_id)
    _ensure_owner(group, user)
    repository.delete_group(session, group)


# ---------------------------------------------------------------- members


def add_member(session: Session, user: User, group_id: int, data: MemberAdd) -> MemberRead:
    group = _get_group(session, group_id)
    _ensure_owner(group, user)
    target = user_repository.get_by_username(session, data.username.lower())
    if target is None:
        raise UserNotFoundError()
    if target.id == group.owner_id or repository.get_member(session, group.id, target.id):
        raise AlreadyMemberError()
    member = repository.save(
        session,
        GroupMember(
            group_id=group.id,
            user_id=target.id,
            can_create=data.can_create,
            can_edit=data.can_edit,
            can_assign=data.can_assign,
        ),
    )
    return _member_read(member, target)


def update_member(
    session: Session, user: User, group_id: int, member_user_id: int, data: MemberUpdate
) -> MemberRead:
    group = _get_group(session, group_id)
    _ensure_owner(group, user)
    member = repository.get_member(session, group.id, member_user_id)
    if member is None:
        raise NotAMemberError()
    member.can_create, member.can_edit, member.can_assign = data.can_create, data.can_edit, data.can_assign
    repository.save(session, member)
    target = user_repository.get_by_id(session, member_user_id)
    return _member_read(member, target)


def remove_member(session: Session, user: User, group_id: int, member_user_id: int) -> None:
    group = _get_group(session, group_id)
    _ensure_owner(group, user)
    member = repository.get_member(session, group.id, member_user_id)
    if member is None:
        raise NotAMemberError()
    repository.delete_row(session, member)


# --------------------------------------------------------------- products


def list_products(session: Session, user: User, group_id: int) -> list[GroupProductRead]:
    group = _get_group(session, group_id)
    _ensure_can_view(session, group, user)
    return [_product_read(p, name) for p, name in repository.list_group_products(session, group.id)]


def create_product(session: Session, user: User, group_id: int, data: ProductCreate) -> GroupProductRead:
    group = _get_group(session, group_id)
    _ensure_permission(session, group, user, GROUP_CREATE)
    product = Product(**data.model_dump(), owner_id=user.id, group_id=group.id)
    return _product_read(repository.save(session, product), None)


def update_product(
    session: Session, user: User, group_id: int, product_id: int, data: ProductUpdate
) -> GroupProductRead:
    group = _get_group(session, group_id)
    _ensure_permission(session, group, user, GROUP_EDIT)
    product = _get_product(session, group, product_id)
    for field, value in data.model_dump().items():
        setattr(product, field, value)
    product.updated_at = utcnow()
    repository.save(session, product)
    assignee = user_repository.get_by_id(session, product.assignee_id) if product.assignee_id else None
    return _product_read(product, assignee.username if assignee else None)


def delete_product(session: Session, user: User, group_id: int, product_id: int) -> None:
    group = _get_group(session, group_id)
    _ensure_owner(group, user)  # only the owner can delete
    repository.delete_row(session, _get_product(session, group, product_id))


def assign_product(
    session: Session, user: User, group_id: int, product_id: int, assignee_id: int | None
) -> GroupProductRead:
    group = _get_group(session, group_id)
    _ensure_permission(session, group, user, GROUP_ASSIGN)
    product = _get_product(session, group, product_id)
    assignee = None
    if assignee_id is not None:
        in_group = assignee_id == group.owner_id or repository.get_member(session, group.id, assignee_id)
        if not in_group:
            raise NotAMemberError()
        assignee = user_repository.get_by_id(session, assignee_id)
    product.assignee_id = assignee_id
    product.updated_at = utcnow()
    repository.save(session, product)
    return _product_read(product, assignee.username if assignee else None)
