"""
Recommendation Engine with Gemini AI Integration.

Maps severity level and environmental context to actionable maintenance
solutions. When Gemini API is configured and available, generates a multimodal
AI-driven engineering action plan. Falls back seamlessly to deterministic
recommendations if the AI service is unconfigured, unreachable, or rate-limited.

⚠ All recommendations are prototype guidance only.
  Final decisions require qualified physical inspection.
  See PRD sections 13 and 30.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from app.services.gemini_service import predict_ai_solution

logger = logging.getLogger(__name__)

PROTOTYPE_DISCLAIMER = (
    "AI-generated prototype guidance. "
    "Final maintenance decisions require qualified physical inspection."
)

GEMINI_DISCLAIMER = (
    "AI-predicted remediation plan (Gemini). "
    "Final maintenance decisions require qualified physical inspection."
)

# Mapping from severity level to recommendation text (deterministic fallback).
_RECOMMENDATIONS: dict[str, str] = {
    "none": (
        "No corrosion indicators detected. Continue routine monitoring schedule."
    ),
    "Low": (
        "Minor corrosion indicators present. Monitor condition and schedule "
        "routine inspection at the next maintenance interval."
    ),
    "Moderate": (
        "Moderate corrosion detected. Perform surface cleaning and inspect "
        "protective coatings. Schedule maintenance within the standard cycle."
    ),
    "High": (
        "Significant corrosion detected. Conduct a detailed maintenance "
        "inspection and corrosion repair assessment. Prioritise within the "
        "current maintenance period."
    ),
    "Critical": (
        "Severe corrosion indicators detected. Immediate professional "
        "structural and maintenance inspection required. Do not defer."
    ),
}


@dataclass
class RecommendationResult:
    severity: str
    recommendation: str
    disclaimer: str = PROTOTYPE_DISCLAIMER
    ai_solution: dict[str, Any] | None = None


def get_recommendation(
    severity: str | None,
    detected: bool,
    image_bytes: bytes | None = None,
    affected_area: float = 0.0,
    temperature: float | None = None,
    humidity: float | None = None,
    environmental_note: str | None = None,
    detections: list[dict[str, Any]] | None = None,
) -> RecommendationResult:
    """
    Return a maintenance recommendation for the given severity level.

    Attempts to generate a Gemini AI solution plan if detected is True.
    Gracefully falls back to deterministic recommendations if AI is
    unavailable.
    """
    if not detected or severity is None:
        key = "none"
        return RecommendationResult(
            severity=severity or "None",
            recommendation=_RECOMMENDATIONS["none"],
            disclaimer=PROTOTYPE_DISCLAIMER,
            ai_solution=None,
        )

    key = severity
    fallback_text = _RECOMMENDATIONS.get(key, _RECOMMENDATIONS["none"])

    # Try Gemini AI solution prediction
    ai_solution = None
    try:
        ai_solution = predict_ai_solution(
            severity=key,
            affected_area=affected_area,
            temperature=temperature,
            humidity=humidity,
            environmental_note=environmental_note,
            detections=detections,
            image_bytes=image_bytes,
        )
    except Exception as exc:
        logger.warning("Gemini AI recommendation failed: %s; using fallback.", exc)

    if ai_solution and ai_solution.get("summary"):
        return RecommendationResult(
            severity=key,
            recommendation=ai_solution["summary"],
            disclaimer=GEMINI_DISCLAIMER,
            ai_solution=ai_solution,
        )

    return RecommendationResult(
        severity=key,
        recommendation=fallback_text,
        disclaimer=PROTOTYPE_DISCLAIMER,
        ai_solution=None,
    )
