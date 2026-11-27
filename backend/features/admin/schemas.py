from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from features.auth.schemas import UserRead


class UserDetail(UserRead):
    ban_reason: str | None = None
    updated_at: datetime


class UserListResponse(BaseModel):
    items: list[UserRead]
    total: int
    page: int
    page_size: int


class BanRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=300)


class RoleChangeRequest(BaseModel):
    role: Literal["user", "admin"]
