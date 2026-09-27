"""
Shared pytest fixtures.
"""
from __future__ import annotations

import io
import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from PIL import Image


# ── Force demo mode ONLY for unit tests (never for production) ────────────

@pytest.fixture(autouse=True, scope="session")
def configure_test_env(tmp_path_factory):
    """Redirect uploads/DB to temp dirs; opt into demo inference for tests only."""
    tmp = tmp_path_factory.mktemp("test_data")
    os.environ["INFERENCE_MODE"] = "demo"  # explicit — production default is real
    os.environ["SQLITE_PATH"] = str(tmp / "test.db")
    os.environ["UPLOAD_DIR"] = str(tmp / "uploads")
    os.environ["MONGODB_URI"] = ""
    os.environ["GEMINI_API_KEY"] = ""  # unit tests run offline; mock tested separately
    # Reset any cached singletons so the test env picks up the new settings
    from app.config import get_settings
    get_settings.cache_clear()
    from app.services.inference import reset_detector
    reset_detector()
    # Reset DB singleton
    import app.database.sqlite_db as sdb
    sdb._repo = None
    yield
    # Teardown: clear caches
    get_settings.cache_clear()
    reset_detector()
    sdb._repo = None


@pytest.fixture(scope="session")
def client(configure_test_env):
    from app.main import create_app
    app = create_app()
    with TestClient(app) as c:
        yield c


@pytest.fixture
def jpeg_image() -> bytes:
    """Return raw bytes of a small JPEG test image."""
    img = Image.new("RGB", (320, 240), color=(160, 90, 60))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture
def png_image() -> bytes:
    img = Image.new("RGB", (200, 150), color=(80, 120, 60))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
