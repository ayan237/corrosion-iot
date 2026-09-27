"""Tests for image utilities — validation and affected-area calculation."""
from __future__ import annotations

import io

import pytest
from PIL import Image

from app.utils.image_utils import (
    ImageValidationError,
    bytes_to_cv2,
    calculate_affected_area,
    validate_image_bytes,
)


# ── Helpers ────────────────────────────────────────────────────────────────

def make_jpeg(w=200, h=150) -> bytes:
    img = Image.new("RGB", (w, h), color=(150, 100, 60))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def make_png(w=200, h=150) -> bytes:
    img = Image.new("RGB", (w, h), color=(80, 120, 60))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ── Validation ─────────────────────────────────────────────────────────────

def test_valid_jpeg_accepted():
    validate_image_bytes(make_jpeg(), "test.jpg")   # should not raise


def test_valid_png_accepted():
    validate_image_bytes(make_png(), "test.png")


def test_bad_extension_rejected():
    with pytest.raises(ImageValidationError, match="Unsupported"):
        validate_image_bytes(make_jpeg(), "malware.exe")


def test_corrupt_bytes_rejected():
    with pytest.raises(ImageValidationError):
        validate_image_bytes(b"not an image at all", "fake.jpg")


def test_empty_bytes_rejected():
    with pytest.raises(ImageValidationError):
        validate_image_bytes(b"", "empty.jpg")


# ── Affected area ─────────────────────────────────────────────────────────

def test_no_detections_returns_zero():
    assert calculate_affected_area([], 200, 150) == 0.0


def test_single_box_correct_area():
    # Box covers exactly half the image: 200x150 → area = 100x75 = 7500 / 30000 = 25%
    dets = [{"class": "corrosion", "confidence": 0.9, "bounding_box": [0, 0, 100, 75]}]
    area = calculate_affected_area(dets, 200, 150)
    assert abs(area - 25.0) < 0.1


def test_overlapping_boxes_no_double_count():
    # Two fully overlapping boxes should give same area as one
    dets = [
        {"class": "corrosion", "confidence": 0.9, "bounding_box": [0, 0, 100, 75]},
        {"class": "corrosion", "confidence": 0.8, "bounding_box": [0, 0, 100, 75]},
    ]
    area = calculate_affected_area(dets, 200, 150)
    assert abs(area - 25.0) < 0.1


def test_partial_overlap_between_two_boxes():
    # Box1: 0,0 → 100,75   (area 7500)
    # Box2: 50,25 → 150,100 (area 7500)
    # Union: x 0→150, y 0→100, BUT L-shaped — easier to just check < sum
    dets = [
        {"class": "corrosion", "confidence": 0.9, "bounding_box": [0, 0, 100, 75]},
        {"class": "corrosion", "confidence": 0.7, "bounding_box": [50, 25, 150, 100]},
    ]
    area = calculate_affected_area(dets, 200, 150)
    # Each box alone = 25%; union must be < 50%
    assert 25.0 < area < 50.0


def test_filter_by_class():
    dets = [
        {"class": "corrosion", "confidence": 0.9, "bounding_box": [0, 0, 100, 75]},
        {"class": "crack",     "confidence": 0.8, "bounding_box": [100, 75, 200, 150]},
    ]
    area_corr  = calculate_affected_area(dets, 200, 150, filter_class="corrosion")
    area_crack  = calculate_affected_area(dets, 200, 150, filter_class="crack")
    area_all    = calculate_affected_area(dets, 200, 150, filter_class=None)
    assert abs(area_corr - 25.0) < 0.1
    assert abs(area_crack - 25.0) < 0.1
    assert abs(area_all - 50.0) < 0.1


def test_boxes_clamped_to_image_bounds():
    # Box extends beyond image — should clamp, not error
    dets = [{"class": "corrosion", "confidence": 0.9, "bounding_box": [-50, -50, 300, 300]}]
    area = calculate_affected_area(dets, 200, 150)
    assert area == 100.0


def test_multiple_non_overlapping_boxes_additive():
    # Two separate 25% boxes = 50%
    dets = [
        {"class": "corrosion", "confidence": 0.9, "bounding_box": [0, 0, 100, 75]},
        {"class": "corrosion", "confidence": 0.8, "bounding_box": [100, 75, 200, 150]},
    ]
    area = calculate_affected_area(dets, 200, 150)
    assert abs(area - 50.0) < 0.5
