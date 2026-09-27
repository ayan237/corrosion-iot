"""
FastAPI application entry point.

Start with:
    uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.inspection import router as inspection_router
from app.config import get_settings
from app.database.repository import get_repository
from app.services.inference import get_detector

# ── Logging ────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan ───────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        repo = get_repository()
        _ = repo.get_statistics()
        logger.info("Database connection: OK")
    except Exception as exc:
        logger.error("Database startup check failed: %s", exc)

    try:
        settings = get_settings()
        logger.info("Loading corrosion model: %s", settings.absolute_model_path)
        detector = get_detector()
        logger.info(
            "Inference mode: %s | model_available=%s",
            detector.mode_name,
            detector.is_available(),
        )
        if detector.mode_name == "demo":
            logger.warning(
                "⚠  Running in DEMO mode — AI detections are simulated. "
                "Set INFERENCE_MODE=real to use backend/models/corrosion.pt."
            )
        elif detector.is_available():
            logger.info("Corrosion model loaded successfully")
    except Exception as exc:
        logger.error("Detector startup check failed: %s", exc)
        raise

    yield
    # Shutdown — nothing to clean up for SQLite


# ── App factory ────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Corrosion Inspection API",
        description=(
            "AI-powered remote corrosion inspection system. "
            "Prototype — not for certified engineering use."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ── CORS ───────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Static file serving for uploaded/annotated images ─────────────────
    uploads_path = settings.upload_path
    app.mount("/uploads", StaticFiles(directory=str(uploads_path)), name="uploads")

    # ── Routers ────────────────────────────────────────────────────────────
    app.include_router(inspection_router)

    # ── Health endpoint ────────────────────────────────────────────────────
    @app.get("/api/health", tags=["health"])
    async def health():
        """Returns API health status including inference mode and database type."""
        detector = get_detector()
        db_type = "mongodb" if settings.mongodb_uri else "sqlite"
        return {
            "status": "ok",
            "inference_mode": detector.mode_name,
            "database": db_type,
            "model_available": detector.is_available(),
        }

    return app


app = create_app()
