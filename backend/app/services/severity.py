"""
Prototype Severity Engine.

⚠ DISCLAIMER: Severity thresholds are prototype estimates for demonstration
purposes. They are NOT certified engineering or industrial standards.
Threshold values are configurable via .env and should be reviewed by domain
experts before any real-world use.

Severity classification is driven primarily by affected area percentage.
Additional factors (region count, confidence, environmental conditions)
produce informational notes and can promote the level by at most ONE step
when explicitly warranted.  This keeps the classification transparent and
auditable.

Outputs: "Low" | "Moderate" | "High" | "Critical"
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from app.config import get_settings

logger = logging.getLogger(__name__)

DISCLAIMER = (
    "Severity is a prototype estimate based on visual coverage and contextual "
    "factors. It is not a certified structural assessment."
)

_LEVELS = ("Low", "Moderate", "High", "Critical")


def _area_to_level(area: float, low_max: float, mod_max: float, high_max: float) -> str:
    """Map affected_area_pct directly to a severity level."""
    if area <= low_max:
        return "Low"
    if area <= mod_max:
        return "Moderate"
    if area <= high_max:
        return "High"
    return "Critical"


def _promote(level: str) -> str:
    """Return the next higher severity level, capped at Critical."""
    idx = _LEVELS.index(level)
    return _LEVELS[min(idx + 1, len(_LEVELS) - 1)]


@dataclass
class SeverityResult:
    level: str          # "Low" | "Moderate" | "High" | "Critical"
    area_level: str     # level based on area alone (for transparency)
    reasoning: str      # human-readable explanation
    promoted: bool      # True if secondary factors raised the level
    disclaimer: str = DISCLAIMER


def estimate_severity(
    affected_area_pct: float,
    num_corrosion_regions: int,
    max_confidence: float,
    environmental_factor: float = 0.0,
) -> SeverityResult:
    """
    Classify severity from visual and contextual inputs.

    Parameters
    ----------
    affected_area_pct : float, 0–100
        Percentage of image covered by corrosion bounding boxes.
    num_corrosion_regions : int
        Number of distinct corrosion detections.
    max_confidence : float, 0–1
        Highest confidence score among corrosion detections.
    environmental_factor : float
        Numeric modifier from environmental context.
        Positive values can trigger a one-level promotion.
        Value range roughly −10 to +10.
    """
    settings = get_settings()

    # ── Step 1: area-based base level ─────────────────────────────────────
    base = _area_to_level(
        affected_area_pct,
        settings.low_max,
        settings.moderate_max,
        settings.high_max,
    )

    # ── Step 2: gather secondary signals ──────────────────────────────────
    upgrade_signals: list[str] = []
    notes: list[str] = []

    # High region count at borderline area warrants attention
    if num_corrosion_regions >= 3:
        upgrade_signals.append(
            f"{num_corrosion_regions} separate corrosion regions detected"
        )

    # Very high confidence at borderline area
    if max_confidence >= 0.90 and affected_area_pct >= (settings.low_max * 0.8):
        notes.append(f"High detection confidence ({max_confidence:.0%})")

    # Environmental factor above a meaningful threshold
    if environmental_factor >= 7.0:
        upgrade_signals.append("Combined elevated temperature and humidity")

    # ── Step 3: optional one-step promotion ───────────────────────────────
    # Promote only if 2 or more independent signals concur AND
    # the area is close to (≥ 80%) the next threshold boundary.
    promoted = False
    level = base

    should_promote = len(upgrade_signals) >= 2
    if should_promote and base != "Critical":
        level = _promote(base)
        promoted = True

    # ── Step 4: human-readable reasoning ──────────────────────────────────
    parts = [f"Affected area: {affected_area_pct:.1f}%"]
    parts.extend(upgrade_signals)
    parts.extend(notes)
    reasoning = ". ".join(parts) + "."
    if promoted:
        reasoning += (
            f" Severity elevated from {base} to {level} "
            f"based on multiple contributing factors."
        )

    logger.debug(
        "Severity: %s (base=%s, area=%.1f%%, regions=%d, conf=%.2f, env=%.1f)",
        level, base, affected_area_pct, num_corrosion_regions,
        max_confidence, environmental_factor,
    )

    return SeverityResult(
        level=level,
        area_level=base,
        reasoning=reasoning,
        promoted=promoted,
    )


def severity_for_no_detection() -> SeverityResult:
    """Return a sentinel result when no corrosion was detected."""
    return SeverityResult(
        level="Low",
        area_level="Low",
        reasoning="No corrosion detected in this inspection.",
        promoted=False,
    )
