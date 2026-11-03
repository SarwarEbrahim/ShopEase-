import os
from collections.abc import Iterator

from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import NullPool


def _database_url() -> str:
    # Local development uses SQLite. In production (Vercel) set DATABASE_URL
    # to the Supabase PostgreSQL connection string.
    url = os.getenv("DATABASE_URL", "sqlite:///./shopease.db")
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


DATABASE_URL = _database_url()

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # NullPool: no long-lived connections, which suits serverless + Supabase pooler.
    engine = create_engine(DATABASE_URL, poolclass=NullPool)


def init_db() -> None:
    """Create the tables if they do not exist yet."""
    # Import the models so SQLModel knows about their tables.
    from features.products import models  # noqa: F401

    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    """FastAPI dependency: one database session per request."""
    with Session(engine) as session:
        yield session
