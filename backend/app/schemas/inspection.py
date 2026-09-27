"""
Pydantic schemas for request/response validation.
These are the contracts between the API layer and the rest of the application.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


# ── Detection item ─────────────────────────────────────────────────────────

class DetectionItem(BaseModel):
    """A single object detection result."""
    cls: str = Field(alias="class", description="Detected class label")
    confidence: float = Field(ge=0.0, le=1.0)
    bounding_box: list[float] = Field(
        description="[x1, y1, x2, y2] pixel coordinates"
    )

    model_config = {"populate_by_name": True}


# ── Inspection response ────────────────────────────────────────────────────

class InspectionResponse(BaseModel):
    """Full inspection result returned to the client."""
    inspection_id: str
    timestamp: str
    device_id: str | None = None

    # Detection
    detected: bool
    detections: list[dict[str, Any]] = []
    affected_area: float = Field(
        description="Estimated affected area percentage (bounding-box based)"
    )

    # Severity
    severity: str | None = None

    # Environment
    temperature: float | None = None
    humidity: float | None = None
    environmental_note: str | None = None

    # Recommendation
    recommendation: str
    recommendation_disclaimer: str | None = None
    ai_solution: dict[str, Any] | None = None

    # Images
    image_reference: str | None = None
    annotated_image_url: str | None = None

    # Inference metadata
    inference_mode: str = Field(
        description="'real' or 'demo' — indicates whether live ML was used"
    )


# ── History list item (summary) ────────────────────────────────────────────

class InspectionSummary(BaseModel):
    inspection_id: str
    timestamp: str
    device_id: str | None = None
    detected: bool
    severity: str | None = None
    confidence: float | None = None
    affected_area: float | None = None
    temperature: float | None = None
    humidity: float | None = None


# ── History response ───────────────────────────────────────────────────────

class HistoryResponse(BaseModel):
    items: list[dict[str, Any]]
    total: int
    page: int
    page_size: int
    pages: int


# ── Statistics response ────────────────────────────────────────────────────

class StatisticsResponse(BaseModel):
    total_inspections: int
    corrosion_detected: int
    no_corrosion: int
    high_critical_cases: int
    critical_cases: int
    detection_rate: float
    avg_confidence: float
    avg_affected_area: float
    severity_distribution: dict[str, int]
    inspection_timeline: list[dict[str, Any]]


# ── Health ─────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    inference_mode: str
    database: str
