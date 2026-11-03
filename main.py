from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from core.database import init_db
from features.products.router import router as products_router
from features.products.service import ProductNotFoundError

# Create the tables on startup (SQLite locally, Supabase PostgreSQL in production).
init_db()

# The docs live under /api because vercel.json only sends /api/* to the backend.
app = FastAPI(
    title="ShopEase API",
    docs_url="/api/docs",
    redoc_url=None,
    openapi_url="/api/openapi.json",
)

app.include_router(products_router)


@app.exception_handler(ProductNotFoundError)
async def product_not_found_handler(
    request: Request, exc: ProductNotFoundError
) -> JSONResponse:
    # Error body shape from the SRS (section 3.6).
    return JSONResponse(
        status_code=404,
        content={"error_code": "PRODUCT_NOT_FOUND", "message": "Product not found"},
    )


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"

# dist/ only exists after `npm run build`; in dev the Vite server serves the UI.
if FRONTEND_DIR.is_dir():
    app.frontend("/", directory=FRONTEND_DIR)
