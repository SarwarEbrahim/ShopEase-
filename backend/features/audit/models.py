from datetime import datetime

from sqlmodel import Field, SQLModel

from core.utils import utcnow

# Event names stored in the activity log
LOGIN = "login"
LOGIN_FAILED = "login_failed"
LOGIN_BLOCKED = "login_blocked"  # banned account or too many attempts
LOGOUT = "logout"
PASSWORD_CHANGE = "password_change"
PASSWORD_CHANGE_FAILED = "password_change_failed"
PROFILE_UPDATE = "profile_update"
ROLE_CHANGE = "role_change"
BAN = "ban"
UNBAN = "unban"
PRODUCT_DELETE = "product_delete"
GROUP_DELETE = "group_delete"
EXPORT = "export"
TOKEN_REFRESH = "token_refresh"
REFRESH_REUSE = "refresh_reuse"  # an old refresh token was used again
SESSION_REVOKE = "session_revoke"


class AuditLog(SQLModel, table=True):
    """The `audit_logs` table: who did what, from which IP and browser, and when."""

    __tablename__ = "audit_logs"

    id: int | None = Field(default=None, primary_key=True)
    event: str = Field(max_length=40, index=True)
    user_id: int | None = Field(default=None, index=True)
    username: str | None = Field(default=None, max_length=60, index=True)
    ip_address: str | None = Field(default=None, max_length=64)
    user_agent: str | None = Field(default=None, max_length=300)
    detail: str | None = Field(default=None, max_length=300)
    created_at: datetime = Field(default_factory=utcnow, index=True)
