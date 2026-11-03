from pathlib import Path

from fastapi import FastAPI

from core.database import init_db

# Create the tables on startup (SQLite locally, Supabase PostgreSQL in production).
init_db()

app = FastAPI(title="ShopEase API")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"

# dist/ only exists after `npm run build`; in dev the Vite server serves the UI.
if FRONTEND_DIR.is_dir():
    app.frontend("/", directory=FRONTEND_DIR)
