"""Tests for the recommendation engine."""
import pytest
from app.services.recommendation import get_recommendation, PROTOTYPE_DISCLAIMER


@pytest.mark.parametrize("severity, detected, keyword", [
    (None,       False, "routine monitoring"),
    ("Low",      True,  "routine inspection"),
    ("Moderate", True,  "protective coating"),
    ("High",     True,  "repair assessment"),
    ("Critical", True,  "Immediate"),
])
def test_recommendations_contain_expected_keywords(severity, detected, keyword):
    rec = get_recommendation(severity, detected)
    assert keyword.lower() in rec.recommendation.lower(), (
        f"Expected '{keyword}' in recommendation for severity={severity}, "
        f"detected={detected}. Got: {rec.recommendation}"
    )


def test_recommendation_includes_disclaimer():
    rec = get_recommendation("High", True)
    assert rec.disclaimer == PROTOTYPE_DISCLAIMER


def test_no_detection_returns_monitoring():
    rec = get_recommendation(None, False)
    assert "monitoring" in rec.recommendation.lower()


def test_all_severity_levels_return_text():
    for level in ("Low", "Moderate", "High", "Critical"):
        rec = get_recommendation(level, True)
        assert len(rec.recommendation) > 20
