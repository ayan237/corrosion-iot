"""Tests for the inference service."""
from __future__ import annotations

import io

import pytest
from PIL import Image

from app.services.inference import DemoDetector, reset_detector


def make_image(color=(120, 80, 50), size=(200, 150)) -> bytes:
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


class TestDemoDetector:
    def setup_method(self):
        reset_detector()

    def test_is_always_available(self):
        assert DemoDetector().is_available() is True

    def test_mode_name_is_demo(self):
        assert DemoDetector().mode_name == "demo"

    def test_predict_returns_detection_result(self):
        det = DemoDetector()
        img = make_image()
        result = det.predict(img)
        assert result.inference_mode == "demo"
        assert isinstance(result.detected, bool)
        assert isinstance(result.detections, list)

    def test_detections_have_required_fields(self):
        det = DemoDetector()
        img = make_image(color=(200, 100, 50))
        result = det.predict(img)
        for d in result.detections:
            assert "class" in d
            assert "confidence" in d
            assert "bounding_box" in d
            assert len(d["bounding_box"]) == 4
            assert 0.0 <= d["confidence"] <= 1.0

    def test_same_image_same_result(self):
        """Demo detector must be deterministic for the same image bytes."""
        det = DemoDetector()
        img = make_image(color=(180, 90, 40))
        r1 = det.predict(img)
        r2 = det.predict(img)
        assert r1.detections == r2.detections

    def test_different_images_may_differ(self):
        """Images with very different content should produce different demo results."""
        det = DemoDetector()
        # Use images with different sizes and varied pixel patterns to maximise hash difference
        images = [
            make_image(color=(c * 50 % 255, c * 30 % 255, c * 70 % 255), size=(100 + c * 20, 80 + c * 15))
            for c in range(1, 8)
        ]
        results = [det.predict(img) for img in images]
        unique = {str(r.detections) for r in results}
        assert len(unique) > 1, "Expected at least 2 different demo results for distinct images"

    def test_image_size_captured(self):
        det = DemoDetector()
        img = make_image(size=(640, 480))
        r = det.predict(img)
        assert r.image_width == 640
        assert r.image_height == 480

    def test_bounding_boxes_within_image(self):
        det = DemoDetector()
        img = make_image(size=(320, 240))
        r = det.predict(img)
        for d in r.detections:
            x1, y1, x2, y2 = d["bounding_box"]
            assert x1 >= 0 and y1 >= 0
            assert x2 <= 320 and y2 <= 240
            assert x2 > x1 and y2 > y1
