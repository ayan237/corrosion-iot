"""
Deterministic Recommendation Engine.

Maps severity level → maintenance recommendation text.
Implemented as a standalone service so it can later be replaced
by a more sophisticated model without touching the pipeline.

⚠ All recommendations are prototype guidance only.
  Final decisions require qualified physical inspection.
  See PRD sections 13 and 30.
"""

from __future__ import annotations

from dataclasses import dataclass

PROTOTYPE_DISCLAIMER = (
    "AI-generated prototype guidance. "
    "Final maintenance decisions require qualified physical inspection."
)

# Mapping from severity level to recommendation text.
# Using a dict instead of if/elif so the mapping is visible as data
# and easy to extend or replace.
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


def get_recommendation(severity: str | None, detected: bool) -> RecommendationResult:
    """
    Return a maintenance recommendation for the given severity level.

    Parameters
    ----------
    severity : str | None
        One of "Low", "Moderate", "High", "Critical" — or None.
    detected : bool
        Whether any corrosion was detected at all.
    """
    if not detected or severity is None:
        key = "none"
    else:
        key = severity

    text = _RECOMMENDATIONS.get(key, _RECOMMENDATIONS["none"])

    return RecommendationResult(
        severity=severity or "None",
        recommendation=text,
    )
