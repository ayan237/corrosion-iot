"""
Inspection API router.

Endpoints:
  POST /api/inspection          — run a new inspection
  GET  /api/inspection/{id}     — fetch a single inspection
  GET  /api/history             — paginated inspection history
  GET  /api/statistics          — dashboard statistics
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from app.database.repository import get_repository
from app.services.environmental import validate_sensor_values
from app.services.pipeline import PipelineError, run_inspection
from app.utils.image_utils import ImageValidationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["inspection"])

# ── Helpers ────────────────────────────────────────────────────────────────

def _sanitise_device_id(device_id: str | None) -> str | None:
    """Strip dangerous characters from device_id."""
    if not device_id:
        return None
    # Keep alphanumerics, underscores, hyphens, dots — max 64 chars
    safe = "".join(c for c in device_id if c.isalnum() or c in "-_.")
    return safe[:64] or None


# ── Run inspection ─────────────────────────────────────────────────────────

@router.post("/inspection", status_code=status.HTTP_201_CREATED)
async def create_inspection(
    image: UploadFile = File(..., description="Corrosion image (JPG/PNG/WEBP)"),
    temperature: Optional[float] = Form(None, description="Ambient temperature °C"),
    humidity: Optional[float] = Form(None, description="Relative humidity %"),
    device_id: Optional[str] = Form(None, description="Optional device identifier"),
):
    """
    Run a full corrosion inspection on the uploaded image.

    Accepts multipart/form-data so the same endpoint works for both:
    - Frontend browser uploads
    - Future hardware device (Arduino / ESP32 / RPi) submissions
    """
    # ── 1. Read image bytes ────────────────────────────────────────────────
    try:
        image_bytes = await image.read()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not read uploaded file: {exc}",
        )

    if not image_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    # ── 2. Validate sensor values ──────────────────────────────────────────
    sensor_errors = validate_sensor_values(temperature, humidity)
    if sensor_errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"message": "Invalid sensor values", "errors": sensor_errors},
        )

    device = _sanitise_device_id(device_id)
    filename = image.filename or "upload.jpg"

    # ── 3. Run pipeline ────────────────────────────────────────────────────
    try:
        record = run_inspection(
            image_bytes=image_bytes,
            filename=filename,
            temperature=temperature,
            humidity=humidity,
            device_id=device,
        )
    except (PipelineError, ImageValidationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        )
    except Exception as exc:
        logger.exception("Unexpected pipeline error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during inspection. Please try again.",
        )

    # ── 4. Persist ────────────────────────────────────────────────────────
    try:
        repo = get_repository()
        repo.save(record)
    except Exception as exc:
        logger.error("Database save failed: %s", exc)
        # Return the result even if DB write fails — don't lose the inspection
        record["_db_warning"] = "Result could not be persisted to database."

    return record


# ── Get single inspection ──────────────────────────────────────────────────

@router.get("/inspection/{inspection_id}")
async def get_inspection(inspection_id: str):
    """Retrieve a previously stored inspection by ID."""
    try:
        repo = get_repository()
        record = repo.get_by_id(inspection_id)
    except Exception as exc:
        logger.error("DB read error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable.",
        )

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inspection '{inspection_id}' not found.",
        )

    return record


# ── History ────────────────────────────────────────────────────────────────

@router.get("/history")
async def get_history(
    page: int = 1,
    page_size: int = 20,
    severity: Optional[str] = None,
    detected: Optional[bool] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
):
    """
    Return paginated inspection history.

    Query parameters:
    - page, page_size  — pagination
    - severity         — filter by severity level (Low/Moderate/High/Critical)
    - detected         — filter by detection status (true/false)
    - date_from        — ISO date string lower bound
    - date_to          — ISO date string upper bound
    """
    if page < 1:
        page = 1
    page_size = max(1, min(page_size, 100))

    valid_severities = {"Low", "Moderate", "High", "Critical"}
    if severity and severity not in valid_severities:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"severity must be one of {sorted(valid_severities)}",
        )

    try:
        repo = get_repository()
        result = repo.list_inspections(
            page=page,
            page_size=page_size,
            severity=severity,
            detected=detected,
            date_from=date_from,
            date_to=date_to,
        )
    except Exception as exc:
        logger.error("History query failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable.",
        )

    return result


# ── Statistics ─────────────────────────────────────────────────────────────

@router.get("/statistics")
async def get_statistics():
    """Return dashboard statistics aggregated over all inspections."""
    try:
        repo = get_repository()
        stats = repo.get_statistics()
    except Exception as exc:
        logger.error("Statistics query failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable.",
        )

    return stats
