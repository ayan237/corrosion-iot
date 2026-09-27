"""
Image preprocessing and validation utilities.

Keeps all OpenCV/Pillow code in one place so the rest of the
application never imports image libraries directly.
"""

from __future__ import annotations

import io
import uuid
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError

from app.config import get_settings

# Allowed MIME types → allowed extensions
ALLOWED_MIME_TYPES: set[str] = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_EXTENSIONS: set[str] = {".jpg", ".jpeg", ".png", ".webp"}


# ── Validation ─────────────────────────────────────────────────────────────

class ImageValidationError(ValueError):
    """Raised when an uploaded file fails validation."""


def validate_image_bytes(data: bytes, filename: str) -> None:
    """
    Raise ImageValidationError if the file is not a supported image.

    Checks:
    - File extension
    - File size limit
    - PIL can actually decode the bytes (catches corrupt files)
    """
    settings = get_settings()

    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ImageValidationError(
            f"Unsupported file extension '{ext}'. "
            f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    if len(data) > settings.max_upload_bytes:
        raise ImageValidationError(
            f"File exceeds maximum size of {settings.max_upload_size_mb} MB."
        )

    try:
        img = Image.open(io.BytesIO(data))
        img.verify()  # checks for corruption without fully decoding
    except (UnidentifiedImageError, Exception) as exc:
        raise ImageValidationError(f"File is not a valid image: {exc}") from exc


# ── Conversion helpers ─────────────────────────────────────────────────────

def bytes_to_cv2(data: bytes) -> np.ndarray:
    """Decode image bytes into a BGR numpy array (OpenCV format)."""
    arr = np.frombuffer(data, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ImageValidationError("OpenCV could not decode the image.")
    return img


def cv2_to_bytes(img: np.ndarray, ext: str = ".jpg") -> bytes:
    """Encode an OpenCV BGR image back to bytes."""
    success, buf = cv2.imencode(ext, img)
    if not success:
        raise RuntimeError("cv2.imencode failed.")
    return buf.tobytes()


def pil_to_cv2(pil_img: Image.Image) -> np.ndarray:
    """Convert a PIL Image (RGB) to an OpenCV BGR array."""
    rgb = np.array(pil_img.convert("RGB"))
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


def cv2_to_pil(bgr: np.ndarray) -> Image.Image:
    """Convert OpenCV BGR array to a PIL Image (RGB)."""
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb)


# ── Preprocessing ──────────────────────────────────────────────────────────

def preprocess_for_model(
    data: bytes,
    target_size: tuple[int, int] | None = None,
) -> tuple[np.ndarray, tuple[int, int]]:
    """
    Decode bytes → BGR array and optionally resize for model input.

    Returns:
        (processed_bgr_array, original_size_wh)
    """
    img = bytes_to_cv2(data)
    original_size = (img.shape[1], img.shape[0])  # (width, height)

    if target_size is not None:
        img = cv2.resize(img, target_size, interpolation=cv2.INTER_LINEAR)

    return img, original_size


# ── Annotation ────────────────────────────────────────────────────────────

# Class-specific colours (BGR)
CLASS_COLOURS: dict[str, tuple[int, int, int]] = {
    "corrosion": (0, 100, 255),   # orange-red
    "crack":     (0, 0, 220),     # red
    "slippage":  (200, 100, 0),   # teal-blue
    "default":   (0, 220, 0),     # green
}

DEMO_LABEL_COLOUR = (180, 180, 0)   # cyan-ish for demo boxes


def draw_detections(
    img_bgr: np.ndarray,
    detections: list[dict],
    demo_mode: bool = False,
) -> np.ndarray:
    """
    Draw bounding boxes and labels on a copy of img_bgr.

    Each detection dict must have:
        class, confidence, bounding_box: [x1, y1, x2, y2]
    """
    out = img_bgr.copy()
    h, w = out.shape[:2]

    for det in detections:
        cls_name = det.get("class", "unknown").lower()
        conf = det.get("confidence", 0.0)
        bb = det.get("bounding_box", [])
        if len(bb) < 4:
            continue

        x1, y1, x2, y2 = [int(v) for v in bb[:4]]
        # Clamp to image bounds
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w - 1, x2), min(h - 1, y2)

        colour = (
            DEMO_LABEL_COLOUR
            if demo_mode
            else CLASS_COLOURS.get(cls_name, CLASS_COLOURS["default"])
        )

        # Box
        cv2.rectangle(out, (x1, y1), (x2, y2), colour, 2)

        # Label background + text
        label = f"{'[DEMO] ' if demo_mode else ''}{cls_name} {conf:.0%}"
        (tw, th), baseline = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1
        )
        label_y = max(y1 - 4, th + baseline)
        cv2.rectangle(
            out,
            (x1, label_y - th - baseline),
            (x1 + tw, label_y + baseline),
            colour,
            cv2.FILLED,
        )
        cv2.putText(
            out, label, (x1, label_y),
            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA,
        )

    return out


# ── Affected area ─────────────────────────────────────────────────────────

def calculate_affected_area(
    detections: list[dict],
    image_width: int,
    image_height: int,
    filter_class: str | None = None,
) -> float:
    """
    Estimate affected area as a percentage of total image area.

    Uses union of bounding boxes to avoid double-counting overlaps.
    Pass filter_class to restrict to a single class; None counts all detections.

    This is an *estimate* based on bounding boxes, not pixel-level segmentation.
    """
    if not detections or image_width <= 0 or image_height <= 0:
        return 0.0

    image_area = image_width * image_height
    if image_area == 0:
        return 0.0

    # Build binary mask to union all boxes (avoids double-counting overlaps)
    mask = np.zeros((image_height, image_width), dtype=np.uint8)

    for det in detections:
        cls = det.get("class", "").lower()
        if filter_class and cls != filter_class.lower():
            continue
        bb = det.get("bounding_box", [])
        if len(bb) < 4:
            continue
        x1, y1, x2, y2 = [int(v) for v in bb[:4]]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(image_width, x2), min(image_height, y2)
        if x2 > x1 and y2 > y1:
            mask[y1:y2, x1:x2] = 1

    union_area = int(mask.sum())
    return round(union_area / image_area * 100.0, 2)


# ── File persistence ───────────────────────────────────────────────────────

def save_upload(data: bytes, original_filename: str) -> tuple[str, str]:
    """
    Save raw upload bytes to the uploads directory with a UUID filename.

    Returns (filename, relative_url_path).
    """
    settings = get_settings()
    ext = Path(original_filename).suffix.lower() or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    dest = settings.upload_path / filename
    dest.write_bytes(data)
    return filename, f"/uploads/{filename}"


def save_annotated(img_bgr: np.ndarray, prefix: str = "ann") -> tuple[str, str]:
    """
    Save an annotated OpenCV image to the uploads directory.

    Returns (filename, relative_url_path).
    """
    settings = get_settings()
    filename = f"{prefix}_{uuid.uuid4().hex}.jpg"
    dest = settings.upload_path / filename
    cv2.imwrite(str(dest), img_bgr)
    return filename, f"/uploads/{filename}"
