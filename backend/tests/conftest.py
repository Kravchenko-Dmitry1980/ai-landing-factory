"""
Test isolation for the whole suite.

- Data goes to a temporary folder, never to backend/data: the settings read these
  variables when app.config is first imported, which happens after this file runs.
- API tests written before accounts existed act as a signed-in administrator.
  Tests of the sign-in itself use the `real_auth` fixture to switch that off.
"""

import atexit
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

_DATA_DIR = Path(tempfile.mkdtemp(prefix="lend-tests-"))
os.environ["DATA_DIR"] = str(_DATA_DIR)
os.environ["UPLOADS_DIR"] = str(_DATA_DIR / "uploads")
os.environ["CONTRACTS_DIR"] = str(_DATA_DIR / "contracts")
os.environ["EXTRACTIONS_DIR"] = str(_DATA_DIR / "extractions")
atexit.register(shutil.rmtree, _DATA_DIR, ignore_errors=True)

from app.core.auth import current_user  # noqa: E402
from app.main import app  # noqa: E402
from app.repositories.account_repository import User  # noqa: E402

TEST_ADMIN = User(
    id="test-admin",
    login="test-admin",
    name="Тестовый администратор",
    role="admin",
    is_active=True,
    created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    last_login_at=None,
)

def _as_test_admin() -> User:
    return TEST_ADMIN


@pytest.fixture(autouse=True)
def _signed_in_admin(request):
    # Set before every test, not once: some tests clear app.dependency_overrides when they finish.
    if "real_auth" in request.fixturenames:
        app.dependency_overrides.pop(current_user, None)
    else:
        app.dependency_overrides[current_user] = _as_test_admin
    yield
    app.dependency_overrides[current_user] = _as_test_admin


@pytest.fixture
def real_auth():
    """Requests go through the real session check for the duration of the test."""
    yield
