"""
Integration tests for the FastAPI endpoints.

Uses TestClient (synchronous) against an in-process app instance
configured with a temp SQLite database and explicit INFERENCE_MODE=demo
(production default is real YOLO; demo is test-only).
"""
from __future__ import annotations

import io

import pytest
from PIL import Image


# ── Helpers ────────────────────────────────────────────────────────────────

def jpeg_bytes(color=(160, 90, 60), size=(320, 240)) -> bytes:
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def png_bytes(size=(200, 150)) -> bytes:
    img = Image.new("RGB", size, color=(80, 120, 60))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def post_inspection(client, image_data, filename="corrosion.jpg",
                    temp=31.4, humidity=72.0, device="CAM_001"):
    return client.post(
        "/api/inspection",
        files={"image": (filename, image_data, "image/jpeg")},
        data={"temperature": str(temp), "humidity": str(humidity), "device_id": device},
    )


# ── Health ─────────────────────────────────────────────────────────────────

class TestHealth:
    def test_returns_ok(self, client):
        r = client.get("/api/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"

    def test_returns_inference_mode(self, client):
        r = client.get("/api/health")
        assert "inference_mode" in r.json()

    def test_returns_database_type(self, client):
        r = client.get("/api/health")
        assert "database" in r.json()

    def test_demo_mode_when_explicitly_configured(self, client):
        r = client.get("/api/health")
        assert r.json()["inference_mode"] == "demo"


# ── Inspection creation ────────────────────────────────────────────────────

class TestCreateInspection:
    def test_valid_jpeg_returns_201(self, client):
        r = post_inspection(client, jpeg_bytes())
        assert r.status_code == 201

    def test_valid_png_accepted(self, client):
        r = client.post(
            "/api/inspection",
            files={"image": ("test.png", png_bytes(), "image/png")},
            data={"temperature": "25.0", "humidity": "55.0"},
        )
        assert r.status_code == 201

    def test_response_has_required_fields(self, client):
        r = post_inspection(client, jpeg_bytes())
        body = r.json()
        for field in [
            "inspection_id", "timestamp", "detected",
            "detections", "affected_area", "severity",
            "recommendation", "inference_mode",
        ]:
            assert field in body, f"Missing field: {field}"

    def test_inspection_id_has_ins_prefix(self, client):
        r = post_inspection(client, jpeg_bytes())
        assert r.json()["inspection_id"].startswith("INS_")

    def test_inference_mode_is_demo_when_configured(self, client):
        r = post_inspection(client, jpeg_bytes())
        assert r.json()["inference_mode"] == "demo"

    def test_temperature_stored(self, client):
        r = post_inspection(client, jpeg_bytes(), temp=28.5)
        assert r.json()["temperature"] == 28.5

    def test_humidity_stored(self, client):
        r = post_inspection(client, jpeg_bytes(), humidity=65.0)
        assert r.json()["humidity"] == 65.0

    def test_device_id_stored(self, client):
        r = post_inspection(client, jpeg_bytes(), device="SENSOR_42")
        assert r.json()["device_id"] == "SENSOR_42"

    def test_affected_area_is_float(self, client):
        r = post_inspection(client, jpeg_bytes())
        assert isinstance(r.json()["affected_area"], (int, float))

    def test_severity_is_valid_level(self, client):
        r = post_inspection(client, jpeg_bytes())
        assert r.json()["severity"] in ("Low", "Moderate", "High", "Critical")

    def test_recommendation_is_string(self, client):
        r = post_inspection(client, jpeg_bytes())
        assert len(r.json()["recommendation"]) > 10

    def test_without_sensor_data_accepted(self, client):
        r = client.post(
            "/api/inspection",
            files={"image": ("c.jpg", jpeg_bytes(), "image/jpeg")},
        )
        assert r.status_code == 201
        body = r.json()
        assert body["temperature"] is None
        assert body["humidity"] is None


# ── Validation error cases ─────────────────────────────────────────────────

class TestInspectionValidation:
    def test_empty_file_rejected(self, client):
        r = client.post(
            "/api/inspection",
            files={"image": ("empty.jpg", b"", "image/jpeg")},
        )
        assert r.status_code in (400, 422)

    def test_non_image_rejected(self, client):
        r = client.post(
            "/api/inspection",
            files={"image": ("script.py", b"print('hi')", "text/plain")},
        )
        assert r.status_code == 422

    def test_corrupt_bytes_rejected(self, client):
        r = client.post(
            "/api/inspection",
            files={"image": ("bad.jpg", b"\xff\xfe\x00\x01bad data", "image/jpeg")},
        )
        assert r.status_code == 422

    def test_temperature_out_of_range_rejected(self, client):
        r = post_inspection(client, jpeg_bytes(), temp=200.0)
        assert r.status_code == 422

    def test_humidity_out_of_range_rejected(self, client):
        r = post_inspection(client, jpeg_bytes(), humidity=110.0)
        assert r.status_code == 422

    def test_negative_humidity_rejected(self, client):
        r = post_inspection(client, jpeg_bytes(), humidity=-5.0)
        assert r.status_code == 422


# ── Retrieval ──────────────────────────────────────────────────────────────

class TestGetInspection:
    def test_retrieve_stored_inspection(self, client):
        create_r = post_inspection(client, jpeg_bytes())
        assert create_r.status_code == 201
        iid = create_r.json()["inspection_id"]

        get_r = client.get(f"/api/inspection/{iid}")
        assert get_r.status_code == 200
        assert get_r.json()["inspection_id"] == iid

    def test_missing_id_returns_404(self, client):
        r = client.get("/api/inspection/DOES_NOT_EXIST")
        assert r.status_code == 404


# ── History ────────────────────────────────────────────────────────────────

class TestHistory:
    def test_returns_200(self, client):
        assert client.get("/api/history").status_code == 200

    def test_response_has_pagination_fields(self, client):
        body = client.get("/api/history").json()
        for f in ["items", "total", "page", "page_size", "pages"]:
            assert f in body

    def test_items_is_list(self, client):
        assert isinstance(client.get("/api/history").json()["items"], list)

    def test_pagination_page_size(self, client):
        body = client.get("/api/history?page=1&page_size=2").json()
        assert body["page_size"] == 2
        assert len(body["items"]) <= 2

    def test_severity_filter_valid(self, client):
        for sev in ("Low", "Moderate", "High", "Critical"):
            r = client.get(f"/api/history?severity={sev}")
            assert r.status_code == 200

    def test_severity_filter_invalid_returns_422(self, client):
        r = client.get("/api/history?severity=INVALID")
        assert r.status_code == 422

    def test_detected_filter_true(self, client):
        r = client.get("/api/history?detected=true")
        assert r.status_code == 200
        for item in r.json()["items"]:
            assert item["detected"] is True

    def test_detected_filter_false(self, client):
        r = client.get("/api/history?detected=false")
        assert r.status_code == 200
        for item in r.json()["items"]:
            assert item["detected"] is False


# ── Statistics ─────────────────────────────────────────────────────────────

class TestStatistics:
    def test_returns_200(self, client):
        assert client.get("/api/statistics").status_code == 200

    def test_has_required_fields(self, client):
        body = client.get("/api/statistics").json()
        for f in [
            "total_inspections", "corrosion_detected", "no_corrosion",
            "high_critical_cases", "detection_rate",
            "avg_confidence", "avg_affected_area",
            "severity_distribution",
        ]:
            assert f in body, f"Missing stats field: {f}"

    def test_total_non_negative(self, client):
        body = client.get("/api/statistics").json()
        assert body["total_inspections"] >= 0

    def test_detection_rate_between_0_and_100(self, client):
        body = client.get("/api/statistics").json()
        assert 0.0 <= body["detection_rate"] <= 100.0
