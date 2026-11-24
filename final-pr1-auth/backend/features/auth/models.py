from datetime import datetime

from sqlmodel import Field, SQLModel

from core.utils import utcnow

ROLE_USER = "user"
ROLE_ADMIN = "admin"


class User(SQLModel, table=True):
    """The `users` table. Passwords are stored only as argon2 hashes."""

    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(max_length=30, unique=True, index=True)
    email: str = Field(max_length=254, unique=True, index=True)
    full_name: str = Field(max_length=100)
    password_hash: str
    role: str = Field(default=ROLE_USER, max_length=20, index=True)
    is_banned: bool = Field(default=False)
    ban_reason: str | None = Field(default=None, max_length=300)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
