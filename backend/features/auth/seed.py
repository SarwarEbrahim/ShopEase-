"""Demo accounts for the assessment: 2 admins and 3 normal users.

The password is NOT in the code. It is read from the SEED_PASSWORD environment
variable (set on Vercel). If the variable is missing, nothing is created.
Running it again is safe: accounts that already exist are skipped.
"""

from sqlmodel import Session

from core import config, security
from core.database import engine
from features.auth import repository
from features.auth.models import ROLE_ADMIN, ROLE_USER, User

DEMO_ACCOUNTS = [
    ("admin1", "Admin One", ROLE_ADMIN),
    ("admin2", "Admin Two", ROLE_ADMIN),
    ("user1", "Demo User One", ROLE_USER),
    ("user2", "Demo User Two", ROLE_USER),
    ("user3", "Demo User Three", ROLE_USER),
]


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
