from datetime import datetime

from pydantic import BaseModel, Field

from features.products.schemas import ProductRead


class GroupName(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class MemberAdd(BaseModel):
    username: str = Field(min_length=1, max_length=30)
    can_create: bool = False
    can_edit: bool = False
    can_assign: bool = False


class MemberUpdate(BaseModel):
    can_create: bool
    can_edit: bool
    can_assign: bool


class MemberRead(BaseModel):
    user_id: int
    username: str
    full_name: str
    can_create: bool
    can_edit: bool
    can_assign: bool


class GroupRead(BaseModel):
    id: int
    name: str
    owner_id: int
    owner_username: str | None = None
    is_owner: bool = False
    my_permissions: list[str] = []  # create / edit / assign
    created_at: datetime


class GroupDetail(GroupRead):
    members: list[MemberRead]


class GroupProductRead(ProductRead):
    assignee_username: str | None = None


class AssignRequest(BaseModel):
    user_id: int | None = None  # None clears the assignment
