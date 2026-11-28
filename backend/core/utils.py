from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(value: datetime) -> datetime:
    """Databases such as SQLite give back datetimes without a time zone. They are UTC."""
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
