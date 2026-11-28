"""All database queries for groups, members and group products."""

from sqlalchemy import func, or_
from sqlmodel import Session, col, select

from features.auth.models import User
from features.groups.models import Group, GroupMember
from features.products.models import Product


def get_group(session: Session, group_id: int) -> Group | None:
    return session.get(Group, group_id)


def save(session: Session, row):
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def groups_for_user(session: Session, user_id: int) -> list[Group]:
    """Groups the user owns or is a member of."""
    member_of = select(GroupMember.group_id).where(col(GroupMember.user_id) == user_id)
    statement = (
        select(Group)
        .where(or_(col(Group.owner_id) == user_id, col(Group.id).in_(member_of)))
        .order_by(col(Group.id))
    )
    return list(session.exec(statement).all())


def all_groups(session: Session, offset: int, limit: int) -> tuple[list[tuple[Group, str | None]], int]:
    statement = select(Group, User.username).join(User, col(User.id) == col(Group.owner_id), isouter=True)
    total = session.exec(select(func.count()).select_from(Group)).one()
    rows = session.exec(statement.order_by(col(Group.id).desc()).offset(offset).limit(limit)).all()
    return [(r[0], r[1]) for r in rows], total


def get_member(session: Session, group_id: int, user_id: int) -> GroupMember | None:
    statement = select(GroupMember).where(
        col(GroupMember.group_id) == group_id, col(GroupMember.user_id) == user_id
    )
    return session.exec(statement).first()


def list_members(session: Session, group_id: int) -> list[tuple[GroupMember, User]]:
    statement = (
        select(GroupMember, User)
        .join(User, col(User.id) == col(GroupMember.user_id))
        .where(col(GroupMember.group_id) == group_id)
        .order_by(col(GroupMember.id))
    )
    return [(r[0], r[1]) for r in session.exec(statement).all()]


def delete_row(session: Session, row) -> None:
    session.delete(row)
    session.commit()


def delete_group(session: Session, group: Group) -> None:
    """Delete the group with its members and its products."""
    for member in session.exec(select(GroupMember).where(col(GroupMember.group_id) == group.id)).all():
        session.delete(member)
    for product in session.exec(select(Product).where(col(Product.group_id) == group.id)).all():
        session.delete(product)
    session.delete(group)
    session.commit()


def list_group_products(session: Session, group_id: int) -> list[tuple[Product, str | None]]:
    statement = (
        select(Product, User.username)
        .join(User, col(User.id) == col(Product.assignee_id), isouter=True)
        .where(col(Product.group_id) == group_id)
        .order_by(col(Product.id).desc())
    )
    return [(r[0], r[1]) for r in session.exec(statement).all()]


def get_group_product(session: Session, group_id: int, product_id: int) -> Product | None:
    product = session.get(Product, product_id)
    if product is None or product.group_id != group_id:
        return None
    return product
