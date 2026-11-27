"""Write one line of the activity log. This helper reads the IP address and the
browser (User-Agent) from the request, so the routers can call it in one line."""

from fastapi import Request
from sqlmodel import Session

from features.audit import repository
from features.audit.models import AuditLog


def client_ip(request: Request) -> str | None:
    # Behind Vercel the real address is the first entry of X-Forwarded-For.
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()[:64]
    return request.client.host if request.client else None


def record(
    session: Session,
    event: str,
    request: Request,
    user=None,
    username: str | None = None,
    detail: str | None = None,
) -> None:
    name = user.username if user is not None else username
    repository.add(
        session,
        AuditLog(
            event=event,
            user_id=user.id if user is not None else None,
            username=name.strip().lower()[:60] if name else None,
            ip_address=client_ip(request),
            user_agent=(request.headers.get("user-agent") or "")[:300] or None,
            detail=detail[:300] if detail else None,
        ),
    )
