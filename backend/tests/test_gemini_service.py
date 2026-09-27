"""Unit tests for Gemini AI solution service."""

import json
from unittest.mock import MagicMock, patch

import pytest
import httpx

from app.services.gemini_service import predict_ai_solution, _build_prompt
from app.services.recommendation import get_recommendation, PROTOTYPE_DISCLAIMER, GEMINI_DISCLAIMER


def test_build_prompt_includes_severity_and_environment():
    prompt = _build_prompt(
        severity="High",
        affected_area=35.5,
        temperature=40.0,
        humidity=85.0,
        environmental_note="Elevated humidity accelerates oxidation.",
        detections=[{"class": "corrosion", "confidence": 0.88}],
    )
    assert "High" in prompt
    assert "35.50%" in prompt
    assert "40.0 °C" in prompt
    assert "85.0 %" in prompt
    assert "Elevated humidity" in prompt


def test_predict_ai_solution_without_key_returns_none():
    result = predict_ai_solution(
        severity="Low",
        affected_area=3.0,
        api_key="",
    )
    assert result is None


def test_predict_ai_solution_success_with_mock():
    mock_payload = {
        "summary": "Mild oxidation detected on outer flange.",
        "immediate_actions": ["Isolate component", "Inspect adjoining fasteners"],
        "surface_preparation": ["Wire brush to St 2 standard", "Solvent degrease"],
        "treatment_and_coating": ["Apply zinc-rich primer", "Polyurethane topcoat"],
        "preventive_schedule": "Re-inspect in 60 days",
        "estimated_urgency": "Medium Priority",
    }
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": json.dumps(mock_payload)}]
                }
            }
        ]
    }

    with patch("httpx.Client.post", return_value=mock_response):
        result = predict_ai_solution(
            severity="Moderate",
            affected_area=12.0,
            api_key="mock_test_key",
            model="gemini-flash-latest",
        )

        assert result is not None
        assert result["summary"] == mock_payload["summary"]
        assert result["immediate_actions"] == mock_payload["immediate_actions"]
        assert result["estimated_urgency"] == "Medium Priority"
        assert result["model_used"] == "gemini-flash-latest"


def test_predict_ai_solution_handles_api_error_gracefully():
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.text = '{"error": "PERMISSION_DENIED"}'

    with patch("httpx.Client.post", return_value=mock_response):
        result = predict_ai_solution(
            severity="High",
            affected_area=45.0,
            api_key="denied_key",
        )
        assert result is None


def test_predict_ai_solution_handles_timeout_gracefully():
    with patch("httpx.Client.post", side_effect=httpx.TimeoutException("Timed out")):
        result = predict_ai_solution(
            severity="Critical",
            affected_area=60.0,
            api_key="mock_key",
        )
        assert result is None


def test_get_recommendation_uses_ai_solution_when_available():
    mock_ai = {
        "summary": "Severe pitting detected. Immediate overhaul needed.",
        "immediate_actions": ["Emergency shutdown"],
        "surface_preparation": ["Grit blast Sa 2.5"],
        "treatment_and_coating": ["Epoxy barrier"],
        "preventive_schedule": "Weekly inspection",
        "estimated_urgency": "Immediate",
    }

    with patch("app.services.recommendation.predict_ai_solution", return_value=mock_ai):
        rec = get_recommendation(severity="Critical", detected=True)
        assert rec.severity == "Critical"
        assert rec.recommendation == mock_ai["summary"]
        assert rec.disclaimer == GEMINI_DISCLAIMER
        assert rec.ai_solution == mock_ai


def test_get_recommendation_falls_back_when_ai_returns_none():
    with patch("app.services.recommendation.predict_ai_solution", return_value=None):
        rec = get_recommendation(severity="Low", detected=True)
        assert rec.severity == "Low"
        assert "routine inspection" in rec.recommendation.lower()
        assert rec.disclaimer == PROTOTYPE_DISCLAIMER
        assert rec.ai_solution is None
