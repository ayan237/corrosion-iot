"""Tests for the severity engine."""
import pytest
from app.services.severity import estimate_severity, severity_for_no_detection


# ── Boundary tests using default thresholds (5 / 20 / 50) ────────────────

@pytest.mark.parametrize("area, expected", [
    (0.0,  "Low"),
    (1.0,  "Low"),
    (4.9,  "Low"),
    (5.0,  "Low"),    # exactly at low_max → still Low
    (5.01, "Moderate"),
    (10.0, "Moderate"),
    (19.9, "Moderate"),
    (20.0, "Moderate"),
    (20.01, "High"),
    (35.0,  "High"),
    (50.0,  "High"),
    (50.01, "Critical"),
    (75.0,  "Critical"),
    (100.0, "Critical"),
])
def test_severity_area_boundaries(area, expected):
    result = estimate_severity(area, num_corrosion_regions=1, max_confidence=0.0)
    assert result.level == expected, (
        f"area={area}% expected {expected} got {result.level}"
    )


def test_severity_no_detection():
    r = severity_for_no_detection()
    assert r.level == "Low"
    assert not r.promoted
    assert "No corrosion" in r.reasoning


def test_severity_promotion_requires_multiple_signals():
    """Two signals (3 regions + high env) should trigger promotion."""
    # Area = 3% → base Low; 3 regions + env=8 → promote to Moderate
    r = estimate_severity(3.0, num_corrosion_regions=3, max_confidence=0.75, environmental_factor=8.0)
    assert r.promoted is True
    assert r.area_level == "Low"
    assert r.level == "Moderate"


def test_severity_single_signal_no_promotion():
    """Only one signal should not promote."""
    r = estimate_severity(3.0, num_corrosion_regions=3, max_confidence=0.5, environmental_factor=0.0)
    assert r.promoted is False


def test_severity_critical_cannot_be_promoted_higher():
    r = estimate_severity(80.0, num_corrosion_regions=5, max_confidence=0.99, environmental_factor=10.0)
    assert r.level == "Critical"


def test_severity_result_has_reasoning():
    r = estimate_severity(15.0, 2, 0.80)
    assert len(r.reasoning) > 0
    assert "15.0%" in r.reasoning


def test_severity_disclaimer_present():
    r = estimate_severity(10.0, 1, 0.7)
    assert len(r.disclaimer) > 0
