"""
Centralised configuration — all tuneable values live here.
Change thresholds, paths, and limits in .env without touching application code.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve the backend root directory
BACKEND_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Database ─────────────────────────────────────────────────────────────
    mongodb_uri: str = ""
    database_name: str = "corrosion_inspection"
    sqlite_path: str = "corrosion.db"

    # ── ML Model ──────────────────────────────────────────────────────────────
    # Relative paths resolve against BACKEND_ROOT (backend/), independent of CWD.
    model_path: str = "models/corrosion.pt"
    roboflow_api_key: str = ""
    # "real"  → always use local YOLO model (default; fail loudly if unavailable)
    # "auto"  → same as real (no silent demo fallback)
    # "demo"  → mock detector only when explicitly requested (e.g. unit tests)
    inference_mode: str = "real"

    # ── Gemini AI Solution ────────────────────────────────────────────────────
    gemini_api_key: str = ""
    gemini_model: str = "gemini-flash-latest"

    # ── File Handling ─────────────────────────────────────────────────────────
    upload_dir: str = "uploads"
    max_upload_size_mb: int = 10

    # ── Severity Thresholds (prototype — NOT engineering standards) ───────────
    low_max: float = 5.0       # affected_area % ≤ this → Low
    moderate_max: float = 20.0  # ≤ this → Moderate
    high_max: float = 50.0      # ≤ this → High  |  above → Critical

    # ── Environmental Thresholds ──────────────────────────────────────────────
    humidity_elevated_threshold: float = 70.0
    temp_high_threshold: float = 35.0

    # ── Input Validation Ranges ───────────────────────────────────────────────
    temp_min: float = -40.0
    temp_max: float = 85.0
    humidity_min: float = 0.0
    humidity_max: float = 100.0

    # ── CORS ──────────────────────────────────────────────────────────────────
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # ── Derived helpers ───────────────────────────────────────────────────────
    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def upload_path(self) -> Path:
        p = Path(self.upload_dir)
        if not p.is_absolute():
            p = BACKEND_ROOT / p
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def absolute_model_path(self) -> Path:
        """Absolute path to corrosion.pt, resolved from backend root."""
        p = Path(self.model_path)
        if not p.is_absolute():
            p = BACKEND_ROOT / p
        return p.resolve()

    @property
    def use_real_inference(self) -> bool:
        # Demo only when explicitly requested; auto/real always mean real YOLO.
        return self.inference_mode != "demo"

    @property
    def sqlite_absolute_path(self) -> Path:
        p = Path(self.sqlite_path)
        if not p.is_absolute():
            p = BACKEND_ROOT / p
        return p

    @field_validator("inference_mode")
    @classmethod
    def validate_inference_mode(cls, v: str) -> str:
        allowed = {"auto", "demo", "real"}
        if v not in allowed:
            raise ValueError(f"inference_mode must be one of {allowed}")
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings singleton."""
    return Settings()
