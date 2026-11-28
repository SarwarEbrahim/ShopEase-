"""Settings read from environment variables.

Secrets are never written in the code. Locally the values have safe-for-development
defaults. In production (when DATABASE_URL is set) the secrets are required, so the
app refuses to start with a default secret.
"""

import os

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "15"))
# The refresh token is a long random string kept in an httpOnly cookie.
REFRESH_TOKEN_DAYS = int(os.getenv("REFRESH_TOKEN_DAYS", "7"))
# The cookie is marked Secure (https only) in production. Locally (http) it cannot be.
COOKIE_SECURE = bool(os.getenv("DATABASE_URL"))


def _secret(name: str, dev_default: str) -> str:
    value = os.getenv(name)
    if value:
        return value
    if os.getenv("DATABASE_URL"):
        raise RuntimeError(f"{name} must be set in production")
    return dev_default


# Signs and verifies the JWT access tokens.
JWT_SECRET = _secret("JWT_SECRET", "dev-only-jwt-secret-change-me-0123456789abcdef")
# Mixed into passwords before hashing (the "pepper").
PASSWORD_PEPPER = _secret("PASSWORD_PEPPER", "dev-only-pepper-change-me-0123456789abcdef")

# Password for the demo accounts (2 admins, 3 users). Set it only on the server;
# when it is not set, no demo accounts are created.
SEED_PASSWORD = os.getenv("SEED_PASSWORD")
