from datetime import datetime

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel

from core.utils import utcnow


class Group(SQLModel, table=True):
    """The `groups` table. The owner is the user who created the group."""

    __tablename__ = "groups"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=80)
    owner_id: int = Field(index=True)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class GroupMember(SQLModel, table=True):
    """The `group_members` table: one row per member with their own permissions.
    The owner is not stored here, the owner can do everything."""

    __tablename__ = "group_members"
    __table_args__ = (UniqueConstraint("group_id", "user_id", name="uq_group_member"),)

    id: int | None = Field(default=None, primary_key=True)
    group_id: int = Field(index=True)
    user_id: int = Field(index=True)
    can_create: bool = Field(default=False)
    can_edit: bool = Field(default=False)
    can_assign: bool = Field(default=False)
    created_at: datetime = Field(default_factory=utcnow)
