"""
Inspection Pipeline Orchestrator.

This is the single entry point for running a full inspection.
It wires together:
  1. Image validation + preprocessing
  2. ML inference (local YOLO; demo only if explicitly enabled)
  3. Affected area calculation
  4. Environmental context assessment
  5. Severity estimation
  6. Recommendation generation
  7. Image annotation + file persistence
  8. Record assembly for storage

The pipeline never touches the database or the HTTP layer — those are
handled by the API router after this function returns.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from app.config import get_settings
from app.services.environmental import assess_environment
from app.services.inference import get_detector
from app.services.recommendation import get_recommendation
from app.services.severity import estimate_severity, severity_for_no_detection
from app.utils.image_utils import (
    bytes_to_cv2,
    calculate_affected_area,
    draw_detections,
    save_annotated,
    save_upload,
    validate_image_bytes,
    ImageValidationError,
)

logger = logging.getLogger(__name__)


class PipelineError(Exception):
    """Raised when the pipeline cannot complete for a known reason."""


def run_inspection(
    image_bytes: bytes,
    filename: str,
    temperature: float | None,
    humidity: float | None,
    device_id: str | None,
) -> dict[str, Any]:
    """
    Execute the full inspection pipeline.

    Parameters
    ----------
    image_bytes : bytes
        Raw bytes of the uploaded image.
    filename : str
        Original filename (used for extension validation and saving).
    temperature : float | None
        Sensor reading in °C (optional).
    humidity : float | None
        Sensor reading in % (optional).
    device_id : str | None
        Identifier of the capturing device (optional).

    Returns
    -------
    dict
        Full inspection record ready to be stored and returned to the client.

    Raises
    ------
    PipelineError
        For expected failure modes (bad image, model unavailable, etc.).
    """
    # ── 1. Validate image ─────────────────────────────────────────────────
    try:
        validate_image_bytes(image_bytes, filename)
    except ImageValidationError as exc:
        raise PipelineError(str(exc)) from exc

    # ── 2. Persist original upload ────────────────────────────────────────
    try:
        _, image_url = save_upload(image_bytes, filename)
    except Exception as exc:
        logger.error("Failed to save upload: %s", exc)
        raise PipelineError("Could not save uploaded image.") from exc

    # ── 3. Run inference ──────────────────────────────────────────────────
    try:
        detector = get_detector()
        result = detector.predict(image_bytes)
    except Exception as exc:
        logger.error("Inference failed: %s", exc)
        raise PipelineError(f"AI inference failed: {exc}") from exc

    # ── 4. Affected area ──────────────────────────────────────────────────
    affected_area = calculate_affected_area(
        result.detections, result.image_width, result.image_height,
        filter_class=None,   # count all detected defect classes
    )

    # ── 5. Environmental context ──────────────────────────────────────────
    env = assess_environment(temperature, humidity)

    # ── 6. Severity ───────────────────────────────────────────────────────
    if result.detected:
        max_conf = max((d["confidence"] for d in result.detections), default=0.0)
        corrosion_count = len(result.detections)
        severity_result = estimate_severity(
            affected_area_pct=affected_area,
            num_corrosion_regions=corrosion_count,
            max_confidence=max_conf,
            environmental_factor=env.priority_modifier,
        )
    else:
        severity_result = severity_for_no_detection()

    # ── 7. Recommendation ─────────────────────────────────────────────────
    rec = get_recommendation(
        severity=severity_result.level,
        detected=result.detected,
        image_bytes=image_bytes,
        affected_area=affected_area,
        temperature=temperature,
        humidity=humidity,
        environmental_note=env.note,
        detections=result.detections,
    )

    # ── 8. Annotate image ─────────────────────────────────────────────────
    try:
        bgr = bytes_to_cv2(image_bytes)
        annotated_bgr = draw_detections(
            bgr, result.detections, demo_mode=(result.inference_mode == "demo")
        )
        _, annotated_url = save_annotated(annotated_bgr)
    except Exception as exc:
        logger.warning("Annotation failed: %s — continuing without annotated image", exc)
        annotated_url = None

    # ── 9. Assemble record ────────────────────────────────────────────────
    inspection_id = f"INS_{uuid.uuid4().hex[:8].upper()}"
    timestamp = datetime.now(timezone.utc).isoformat()

    # Top-level confidence (highest from all detections)
    top_confidence = (
        max((d["confidence"] for d in result.detections), default=None)
        if result.detections else None
    )

    record: dict[str, Any] = {
        "inspection_id": inspection_id,
        "timestamp": timestamp,
        "device_id": device_id,

        # Detection
        "detected": result.detected,
        "detections": result.detections,
        "confidence": top_confidence,

        # Area + severity
        "affected_area": affected_area,
        "severity": severity_result.level,
        "severity_reasoning": severity_result.reasoning,

        # Environment
        "temperature": temperature,
        "humidity": humidity,
        "environmental_note": env.note,

        # Recommendation
        "recommendation": rec.recommendation,
        "recommendation_disclaimer": rec.disclaimer,
        "ai_solution": rec.ai_solution,

        # Files
        "image_reference": image_url,
        "annotated_image_url": annotated_url,

        # Metadata
        "inference_mode": result.inference_mode,
    }

    logger.info(
        "Inspection %s complete — detected=%s, severity=%s, mode=%s",
        inspection_id, result.detected, severity_result.level, result.inference_mode,
    )

    return record
