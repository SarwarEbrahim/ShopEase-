"""Demo accounts and sample data for the assessment: 2 admins, 3 normal users and
a few products owned by the normal users.

The password is NOT in the code. It is read from the SEED_PASSWORD environment
variable (set on Vercel). If the variable is missing, nothing is created.
Running it again is safe: accounts that already exist are skipped.
"""

from decimal import Decimal

from sqlmodel import Session, col, select

from core import config, security
from core.database import engine
from features.auth import repository
from features.auth.models import ROLE_ADMIN, ROLE_USER, User
from features.groups.models import Group, GroupMember
from features.products.models import Product

DEMO_ACCOUNTS = [
    ("admin1", "Admin One", ROLE_ADMIN),
    ("admin2", "Admin Two", ROLE_ADMIN),
    ("user1", "Demo User One", ROLE_USER),
    ("user2", "Demo User Two", ROLE_USER),
    ("user3", "Demo User Three", ROLE_USER),
]


# username -> (name, category, price, stock)
SAMPLE_PRODUCTS = {
    "user1": [("Blue Notebook", "Stationery", "120.00", 50), ("Desk Lamp", "Home", "850.00", 15)],
    "user2": [("Running Shoes", "Sports", "3200.00", 12), ("Water Bottle", "Sports", "450.00", 80)],
    "user3": [("Phone Case", "Electronics", "350.00", 60), ("USB Cable", "Electronics", "220.00", 120)],
}


def seed_demo_accounts() -> None:
    if not config.SEED_PASSWORD:
        return
    with Session(engine) as session:
        for username, full_name, role in DEMO_ACCOUNTS:
            if repository.get_by_username(session, username):
                continue
            repository.save(
                session,
                User(
                    username=username,
                    email=f"{username}@shopease.example",
                    full_name=full_name,
                    password_hash=security.hash_password(config.SEED_PASSWORD),
                    role=role,
                ),
            )

        _seed_products(session)
        _seed_group(session)


def _seed_products(session: Session) -> None:
    # Products from the mid project have no owner yet: give them to admin1.
    admin1 = repository.get_by_username(session, "admin1")
    if admin1 is not None:
        orphans = session.exec(select(Product).where(col(Product.owner_id).is_(None))).all()
        for product in orphans:
            product.owner_id = admin1.id
            session.add(product)

    # Sample data: two products for each demo user (only if they own none yet).
    for username, items in SAMPLE_PRODUCTS.items():
        user = repository.get_by_username(session, username)
        if user is None:
            continue
        owns_any = session.exec(select(Product).where(col(Product.owner_id) == user.id).limit(1)).first()
        if owns_any is not None:
            continue
        for name, category, price, stock in items:
            session.add(
                Product(name=name, category=category, price=Decimal(price), stock=stock, owner_id=user.id)
            )
    session.commit()


def _seed_group(session: Session) -> None:
    """One shared group with mixed permissions (owner user1, members user2 and user3)."""
    if session.exec(select(Group).where(col(Group.name) == "Demo Team")).first():
        return
    owner = repository.get_by_username(session, "user1")
    member_a = repository.get_by_username(session, "user2")
    member_b = repository.get_by_username(session, "user3")
    if owner is None or member_a is None or member_b is None:
        return
    group = Group(name="Demo Team", owner_id=owner.id)
    session.add(group)
    session.commit()
    session.refresh(group)
    # user2 may create and edit; user3 may only assign.
    session.add(GroupMember(group_id=group.id, user_id=member_a.id, can_create=True, can_edit=True, can_assign=False))
    session.add(GroupMember(group_id=group.id, user_id=member_b.id, can_create=False, can_edit=False, can_assign=True))
    for name, category, price, stock in [("Team Whiteboard", "Office", "1500.00", 3), ("Shared Projector", "Electronics", "28000.00", 1)]:
        session.add(Product(name=name, category=category, price=Decimal(price), stock=stock, owner_id=owner.id, group_id=group.id))
    session.commit()
