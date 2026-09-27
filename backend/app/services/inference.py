"""
ML Inference Service — Corrosion Object Detection.

Architecture:
  CorrosionDetector (abstract interface)
    ├── YOLODetector       — real inference via Ultralytics YOLOv8
    └── DemoDetector       — deterministic mock (tests only; never default)

The rest of the application only depends on CorrosionDetector.predict().
Model-specific code is entirely contained here.

IMPORTANT:
  Production / normal app startup ALWAYS uses YOLODetector.
  DemoDetector is only selected when INFERENCE_MODE=demo is set explicitly
  (e.g. unit tests). There is no silent fallback to mock detections.
"""

from __future__ import annotations

import logging
import random
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import numpy as np

from app.config import get_settings

logger = logging.getLogger(__name__)

# Inference thresholds for the trained corrosion.pt model
YOLO_IMGSZ = 640
YOLO_CONF = 0.10
YOLO_IOU = 0.45


# ── Detection result dataclass ─────────────────────────────────────────────

class DetectionResult:
    """Output of one inference call."""

    def __init__(
        self,
        detections: list[dict[str, Any]],
        inference_mode: str,
        image_width: int,
        image_height: int,
    ) -> None:
        self.detections = detections      # list of {class, confidence, bounding_box}
        self.inference_mode = inference_mode   # "real" | "demo"
        self.image_width = image_width
        self.image_height = image_height

    @property
    def detected(self) -> bool:
        return len(self.detections) > 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "detections": self.detections,
            "detected": self.detected,
            "inference_mode": self.inference_mode,
        }


# ── Abstract interface ─────────────────────────────────────────────────────

class CorrosionDetector(ABC):
    """
    All detectors must implement this interface.
    The pipeline never calls any method other than predict() and is_available().
    """

    @abstractmethod
    def predict(self, image_bytes: bytes) -> DetectionResult:
        """Run detection on raw image bytes. Returns DetectionResult."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the detector is ready to run inference."""
        ...

    @property
    @abstractmethod
    def mode_name(self) -> str:
        """Return 'real' or 'demo'."""
        ...


# ── YOLO detector (real inference) ────────────────────────────────────────

class YOLODetector(CorrosionDetector):
    """
    YOLOv8 detector via Ultralytics.

    Loads the local trained weights at backend/models/corrosion.pt
    (or MODEL_PATH). Class names come from the model checkpoint itself.
    """

    def __init__(self, model_path: str | Path, *, require: bool = True) -> None:
        self._model_path = Path(model_path).resolve()
        self._model = None
        self._load_error: str | None = None
        self._load(require=require)

    def _load(self, *, require: bool) -> None:
        logger.info("Loading corrosion model: %s", self._model_path)

        if not self._model_path.exists():
            self._load_error = f"Model file not found: {self._model_path}"
            if require:
                raise RuntimeError(
                    f"Real corrosion model could not be loaded: {self._load_error}"
                )
            logger.error(self._load_error)
            return

        try:
            from ultralytics import YOLO  # type: ignore
            self._model = YOLO(str(self._model_path))
            logger.info("Corrosion model loaded successfully")
        except ImportError as exc:
            self._load_error = (
                "ultralytics package is not installed. "
                "Run: pip install ultralytics"
            )
            if require:
                raise RuntimeError(
                    f"Real corrosion model could not be loaded: {self._load_error}"
                ) from exc
            logger.error(self._load_error)
        except Exception as exc:
            self._load_error = str(exc)
            if require:
                raise RuntimeError(
                    f"Real corrosion model could not be loaded: {self._load_error}"
                ) from exc
            logger.error("Failed to load YOLO model: %s", self._load_error)

    def is_available(self) -> bool:
        return self._model is not None

    @property
    def mode_name(self) -> str:
        return "real"

    def predict(self, image_bytes: bytes) -> DetectionResult:
        if not self.is_available():
            raise RuntimeError(
                f"Real corrosion model could not be loaded: {self._load_error}"
            )

        import cv2
        arr = np.frombuffer(image_bytes, dtype=np.uint8)
        img_bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img_bgr is None:
            raise ValueError("Could not decode image bytes for inference.")

        h, w = img_bgr.shape[:2]

        results = self._model.predict(
            source=img_bgr,
            imgsz=YOLO_IMGSZ,
            conf=YOLO_CONF,
            iou=YOLO_IOU,
            verbose=False,
        )

        detections: list[dict[str, Any]] = []
        for result in results:
            if result.boxes is None:
                continue
            names = result.names  # dict {int: str} from the trained model
            for box in result.boxes:
                cls_id = int(box.cls[0])
                cls_name = names.get(cls_id, f"class_{cls_id}")
                conf = float(box.conf[0])
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                detections.append({
                    # Preserve model class names; lowercase for API consistency
                    "class": str(cls_name).lower(),
                    "confidence": round(conf, 4),
                    "bounding_box": [
                        round(x1, 1), round(y1, 1),
                        round(x2, 1), round(y2, 1),
                    ],
                })

        return DetectionResult(
            detections=detections,
            inference_mode="real",
            image_width=w,
            image_height=h,
        )


# ── Demo detector (tests only — explicitly disabled by default) ───────────

_DEMO_CLASSES = ["corrosion", "crack", "slippage"]


class DemoDetector(CorrosionDetector):
    """
    Deterministic mock detector for unit tests only.

    ⚠ THIS IS NOT REAL AI INFERENCE ⚠

    Only used when INFERENCE_MODE=demo is set explicitly.
    Never selected by default and never used as a silent fallback.
    """

    def is_available(self) -> bool:
        return True

    @property
    def mode_name(self) -> str:
        return "demo"

    def predict(self, image_bytes: bytes) -> DetectionResult:
        import cv2

        arr = np.frombuffer(image_bytes, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Could not decode image bytes.")

        h, w = img.shape[:2]

        seed = int(sum(image_bytes[:256])) % 10000
        rng = random.Random(seed)

        if rng.random() < 0.20:
            return DetectionResult(
                detections=[],
                inference_mode="demo",
                image_width=w,
                image_height=h,
            )

        n = rng.randint(1, 3)
        detections: list[dict[str, Any]] = []
        for _ in range(n):
            cls = rng.choice(_DEMO_CLASSES)
            conf = round(rng.uniform(0.55, 0.95), 2)

            margin_w = int(w * 0.05)
            margin_h = int(h * 0.05)
            min_box_w = max(int(w * 0.10), 20)
            min_box_h = max(int(h * 0.10), 20)

            x1 = rng.randint(margin_w, max(margin_w, w - min_box_w - margin_w))
            y1 = rng.randint(margin_h, max(margin_h, h - min_box_h - margin_h))
            x2 = min(w - margin_w, x1 + rng.randint(min_box_w, max(min_box_w, w // 2)))
            y2 = min(h - margin_h, y1 + rng.randint(min_box_h, max(min_box_h, h // 2)))

            detections.append({
                "class": cls,
                "confidence": conf,
                "bounding_box": [float(x1), float(y1), float(x2), float(y2)],
            })

        return DetectionResult(
            detections=detections,
            inference_mode="demo",
            image_width=w,
            image_height=h,
        )


# ── Factory ────────────────────────────────────────────────────────────────

_detector: CorrosionDetector | None = None


def get_detector() -> CorrosionDetector:
    """
    Return the detector based on settings.

    Resolution:
    1. inference_mode = "demo"  → DemoDetector (explicit opt-in only, e.g. tests)
    2. otherwise ("real" or "auto") → YOLODetector; raise if model cannot load

    There is no silent fallback to demo/mock detections.
    """
    global _detector
    if _detector is not None:
        return _detector

    settings = get_settings()

    if settings.inference_mode == "demo":
        logger.warning(
            "Inference mode: demo (INFERENCE_MODE=demo) — "
            "detections are simulated; not for production use."
        )
        _detector = DemoDetector()
        return _detector

    # Default / real / auto: always require the real local YOLO model
    model_path = settings.absolute_model_path
    logger.info("Inference mode: real — loading model from %s", model_path)
    _detector = YOLODetector(model_path, require=True)
    return _detector


def reset_detector() -> None:
    """Reset the cached detector — useful in tests."""
    global _detector
    _detector = None
