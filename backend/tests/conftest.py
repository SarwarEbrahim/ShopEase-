"""Test setup. The environment is prepared BEFORE the app is imported, so the tests use
their own temporary SQLite database and never touch the real (Supabase) database."""

import os
import tempfile
from pathlib import Path

_dir = Path(tempfile.mkdtemp(prefix="shopease-test-"))
os.environ["DATABASE_URL"] = f"sqlite:///{(_dir / 'test.db').as_posix()}"
os.environ["JWT_SECRET"] = "test-jwt-secret-0123456789abcdef0123456789"
os.environ["PASSWORD_PEPPER"] = "test-pepper-0123456789abcdef0123456789"
os.environ["SEED_PASSWORD"] = "Seed12345"  # demo accounts (admin1, user1, ...) for the tests

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from core import config  # noqa: E402
from main import app  # noqa: E402

config.COOKIE_SECURE = False  # the test client talks plain http


@pytest.fixture
def client():
    """A fresh client (and so a fresh cookie jar) for every test."""
    return TestClient(app)


@pytest.fixture
def make_client():
    """Build more clients in one test, to act as several devices or users."""
    return lambda: TestClient(app)
