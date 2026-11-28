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
    from features.auth import models as auth_models  # noqa: F401
    from features.audit import models as audit_models  # noqa: F401
    from features.groups import models as group_models  # noqa: F401
    from features.products import models as product_models  # noqa: F401

    SQLModel.metadata.create_all(engine)
    _migrate()


def _migrate() -> None:
    """create_all never changes a table that already exists, so columns added later
    to `products` are added here by hand. It is safe to run on every start."""
    from sqlalchemy import inspect, text

    if "products" not in inspect(engine).get_table_names():
        return
    columns = {c["name"] for c in inspect(engine).get_columns("products")}
    with engine.begin() as conn:
        for name in ("owner_id", "group_id", "assignee_id"):
            if name not in columns:
                conn.execute(text(f"ALTER TABLE products ADD COLUMN {name} INTEGER"))
            conn.execute(text(f"CREATE INDEX IF NOT EXISTS ix_products_{name} ON products ({name})"))


def get_session() -> Iterator[Session]:
    """FastAPI dependency: one database session per request."""
    with Session(engine) as session:
        yield session
