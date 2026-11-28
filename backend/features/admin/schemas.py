from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from features.auth.schemas import UserRead
from features.products.schemas import ProductRead


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


class StatsResponse(BaseModel):
    total_users: int
    banned_users: int
    admins: int
    total_products: int
    total_groups: int
    new_users_7d: int
    new_products_7d: int
    failed_logins_24h: int


class AuditRead(BaseModel):
    id: int
    event: str
    user_id: int | None
    username: str | None
    ip_address: str | None
    user_agent: str | None
    detail: str | None
    created_at: datetime


class AuditListResponse(BaseModel):
    items: list[AuditRead]
    total: int
    page: int
    page_size: int


class CountItem(BaseModel):
    key: str
    count: int


class SecurityOverview(BaseModel):
    """Failed logins in the last 24 hours."""

    by_ip: list[CountItem]
    by_account: list[CountItem]


class AdminProductRead(ProductRead):
    owner_username: str | None = None


class AdminProductList(BaseModel):
    items: list[AdminProductRead]
    total: int
    page: int
    page_size: int


class IdsRequest(BaseModel):
    ids: list[int] = Field(min_length=1, max_length=200)


class BulkBanRequest(IdsRequest):
    reason: str = Field(min_length=1, max_length=300)


class BulkResult(BaseModel):
    updated: int
    skipped: int


class AdminGroupRead(BaseModel):
    id: int
    name: str
    owner_id: int
    owner_username: str | None = None
    created_at: datetime


class AdminGroupList(BaseModel):
    items: list[AdminGroupRead]
    total: int
    page: int
    page_size: int
