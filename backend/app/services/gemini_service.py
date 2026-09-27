"""
Gemini AI Solution Service.

Generates AI-powered maintenance solutions and engineering action plans
based on detected corrosion severity, affected surface area, environmental
conditions (temperature/humidity), and multimodal image inspection.

Falls back gracefully to deterministic guidance if Gemini API is
unavailable, unconfigured, or rate-limited.
"""

from __future__ import annotations

import base64
import json
import logging
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

# Resilient models to try in order if the primary experiences high demand / 503
FALLBACK_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-flash-latest",
    "gemini-3.1-flash-lite",
]


def _build_prompt(
    severity: str,
    affected_area: float,
    temperature: float | None,
    humidity: float | None,
    environmental_note: str | None,
    detections: list[dict[str, Any]] | None,
) -> str:
    temp_str = f"{temperature:.1f} °C" if temperature is not None else "Not provided"
    hum_str = f"{humidity:.1f} %" if humidity is not None else "Not provided"
    env_note_str = environmental_note or "None"
    defect_count = len(detections) if detections else 1

    return f"""You are a certified materials degradation and structural integrity engineer.
Analyze the following corrosion inspection data and image to provide an actionable, industrial-grade maintenance and remediation plan.

### Inspection Parameters:
- Severity Level: {severity}
- Estimated Affected Surface Area: {affected_area:.2f}%
- Defect Regions Detected: {defect_count}
- Ambient Temperature: {temp_str}
- Relative Humidity: {hum_str}
- Environmental Risk Factor: {env_note_str}

### Instructions:
Provide a precise engineering remediation solution tailored to this specific severity and environment.
Take into account high humidity (corrosion acceleration) or temperature extremes if present.
Return strictly valid JSON matching this schema:
{{
  "summary": "Concise 2-3 sentence executive summary of the degradation state and priority remediation required.",
  "immediate_actions": ["Specific immediate action item 1", "Specific immediate action item 2"],
  "surface_preparation": ["Surface prep step e.g. wire brushing, grit blasting to ISO standards, degreasing"],
  "treatment_and_coating": ["Recommended rust converter, anti-corrosive primer (zinc/epoxy), and topcoat systems suited to the ambient environment"],
  "preventive_schedule": "Recommended re-inspection interval and preventive monitoring protocol (e.g. 15-day / 30-day / 90-day cycle)",
  "estimated_urgency": "Immediate | High Priority | Medium Priority | Scheduled Maintenance"
}}
"""


def predict_ai_solution(
    severity: str,
    affected_area: float,
    temperature: float | None = None,
    humidity: float | None = None,
    environmental_note: str | None = None,
    detections: list[dict[str, Any]] | None = None,
    image_bytes: bytes | None = None,
    api_key: str | None = None,
    model: str | None = None,
    timeout: float = 15.0,
) -> dict[str, Any] | None:
    """
    Generate an AI solution plan using Google Gemini API.

    Returns a structured dictionary or None if generation fails or is disabled.
    """
    settings = get_settings()
    key = api_key or settings.gemini_api_key

    if not key or not key.strip():
        logger.debug("Gemini API key not configured; skipping AI solution.")
        return None

    primary_model = model or settings.gemini_model or "gemini-3.5-flash-lite"
    models_to_try = [primary_model] + [m for m in FALLBACK_MODELS if m != primary_model]

    prompt_text = _build_prompt(
        severity=severity,
        affected_area=affected_area,
        temperature=temperature,
        humidity=humidity,
        environmental_note=environmental_note,
        detections=detections,
    )

    parts: list[dict[str, Any]] = []

    # Attach image if provided
    if image_bytes and len(image_bytes) > 0:
        b64_image = base64.b64encode(image_bytes).decode("utf-8")
        parts.append(
            {
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": b64_image,
                }
            }
        )

    parts.append({"text": prompt_text})

    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.2,
        },
    }

    with httpx.Client(timeout=timeout) as client:
        for m_name in models_to_try:
            url = f"{GEMINI_API_BASE}/{m_name}:generateContent?key={key.strip()}"
            try:
                resp = client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if not candidates:
                        continue

                    raw_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    if not raw_text:
                        continue

                    solution = json.loads(raw_text)
                    solution["model_used"] = m_name
                    return solution

                elif resp.status_code in (503, 429):
                    logger.info("Model %s unavailable (%d); trying fallback model...", m_name, resp.status_code)
                    continue
                else:
                    logger.warning("Gemini API error on %s (%d): %s", m_name, resp.status_code, resp.text[:200])
                    # If permission denied or bad request, don't keep failing on other models
                    if resp.status_code in (401, 403, 400):
                        return None
            except (httpx.TimeoutException, httpx.RequestError) as exc:
                logger.warning("Network issue calling Gemini model %s: %s", m_name, exc)
                continue
            except json.JSONDecodeError as exc:
                logger.warning("Failed to decode JSON from %s: %s", m_name, exc)
                continue

    return None
