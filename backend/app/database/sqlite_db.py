"""
SQLite database layer — used when MongoDB is not configured.

All persistence goes through the Repository interface defined here so that
the rest of the application never calls SQLite or MongoDB directly.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import get_settings

_lock = threading.Lock()


# ── Schema ─────────────────────────────────────────────────────────────────

DDL = """
CREATE TABLE IF NOT EXISTS inspections (
    inspection_id        TEXT PRIMARY KEY,
    timestamp            TEXT NOT NULL,
    device_id            TEXT,
    temperature          REAL,
    humidity             REAL,
    image_reference      TEXT,
    annotated_image_ref  TEXT,
    detected             INTEGER NOT NULL DEFAULT 0,
    detections           TEXT,          -- JSON array
    detected_class       TEXT,
    confidence           REAL,
    affected_area        REAL,
    severity             TEXT,
    recommendation       TEXT,
    environmental_note   TEXT,
    raw_result           TEXT           -- full JSON snapshot
);

CREATE INDEX IF NOT EXISTS idx_timestamp   ON inspections (timestamp);
CREATE INDEX IF NOT EXISTS idx_severity    ON inspections (severity);
CREATE INDEX IF NOT EXISTS idx_detected    ON inspections (detected);
"""


# ── Connection helper ──────────────────────────────────────────────────────

def _db_path() -> Path:
    return get_settings().sqlite_absolute_path


@contextmanager
def _get_conn():
    conn = sqlite3.connect(str(_db_path()), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Create tables if they don't exist."""
    with _lock, _get_conn() as conn:
        conn.executescript(DDL)


# ── Repository ─────────────────────────────────────────────────────────────

class InspectionRepository:
    """Thin data-access layer for inspections."""

    def save(self, record: dict[str, Any]) -> dict[str, Any]:
        detections_json = json.dumps(record.get("detections", []))
        raw_json = json.dumps(record)

        # Derive convenience denormalised fields
        detections = record.get("detections", [])
        top = detections[0] if detections else {}

        with _lock, _get_conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO inspections (
                    inspection_id, timestamp, device_id,
                    temperature, humidity,
                    image_reference, annotated_image_ref,
                    detected, detections, detected_class,
                    confidence, affected_area, severity,
                    recommendation, environmental_note, raw_result
                ) VALUES (
                    :inspection_id, :timestamp, :device_id,
                    :temperature, :humidity,
                    :image_reference, :annotated_image_ref,
                    :detected, :detections, :detected_class,
                    :confidence, :affected_area, :severity,
                    :recommendation, :environmental_note, :raw_result
                )
                """,
                {
                    "inspection_id": record["inspection_id"],
                    "timestamp": record.get("timestamp", datetime.now(timezone.utc).isoformat()),
                    "device_id": record.get("device_id"),
                    "temperature": record.get("temperature"),
                    "humidity": record.get("humidity"),
                    "image_reference": record.get("image_reference"),
                    "annotated_image_ref": record.get("annotated_image_url"),
                    "detected": 1 if record.get("detected") else 0,
                    "detections": detections_json,
                    "detected_class": top.get("class"),
                    "confidence": top.get("confidence"),
                    "affected_area": record.get("affected_area"),
                    "severity": record.get("severity"),
                    "recommendation": record.get("recommendation"),
                    "environmental_note": record.get("environmental_note"),
                    "raw_result": raw_json,
                },
            )
        return record

    def get_by_id(self, inspection_id: str) -> dict[str, Any] | None:
        with _get_conn() as conn:
            row = conn.execute(
                "SELECT raw_result FROM inspections WHERE inspection_id = ?",
                (inspection_id,),
            ).fetchone()
        if row is None:
            return None
        return json.loads(row["raw_result"])

    def list_inspections(
        self,
        page: int = 1,
        page_size: int = 20,
        severity: str | None = None,
        detected: bool | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> dict[str, Any]:
        conditions: list[str] = []
        params: list[Any] = []

        if severity:
            conditions.append("severity = ?")
            params.append(severity)
        if detected is not None:
            conditions.append("detected = ?")
            params.append(1 if detected else 0)
        if date_from:
            conditions.append("timestamp >= ?")
            params.append(date_from)
        if date_to:
            conditions.append("timestamp <= ?")
            params.append(date_to)

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        with _get_conn() as conn:
            total = conn.execute(
                f"SELECT COUNT(*) FROM inspections {where}", params
            ).fetchone()[0]

            offset = (page - 1) * page_size
            rows = conn.execute(
                f"SELECT raw_result FROM inspections {where} "
                f"ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                params + [page_size, offset],
            ).fetchall()

        items = [json.loads(r["raw_result"]) for r in rows]
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": max(1, -(-total // page_size)),  # ceiling division
        }

    def get_statistics(self) -> dict[str, Any]:
        with _get_conn() as conn:
            total = conn.execute("SELECT COUNT(*) FROM inspections").fetchone()[0]
            detected = conn.execute(
                "SELECT COUNT(*) FROM inspections WHERE detected = 1"
            ).fetchone()[0]
            high_critical = conn.execute(
                "SELECT COUNT(*) FROM inspections WHERE severity IN ('High','Critical')"
            ).fetchone()[0]
            critical = conn.execute(
                "SELECT COUNT(*) FROM inspections WHERE severity = 'Critical'"
            ).fetchone()[0]
            avg_confidence = conn.execute(
                "SELECT AVG(confidence) FROM inspections WHERE confidence IS NOT NULL"
            ).fetchone()[0]
            avg_area = conn.execute(
                "SELECT AVG(affected_area) FROM inspections WHERE affected_area IS NOT NULL"
            ).fetchone()[0]

            # Severity distribution
            sev_rows = conn.execute(
                """
                SELECT severity, COUNT(*) as cnt
                FROM inspections
                WHERE severity IS NOT NULL
                GROUP BY severity
                """
            ).fetchall()

            # Recent 30 days inspection counts grouped by date
            timeline_rows = conn.execute(
                """
                SELECT date(timestamp) as day, COUNT(*) as cnt
                FROM inspections
                WHERE timestamp >= date('now', '-30 days')
                GROUP BY day
                ORDER BY day
                """
            ).fetchall()

        return {
            "total_inspections": total,
            "corrosion_detected": detected,
            "no_corrosion": total - detected,
            "high_critical_cases": high_critical,
            "critical_cases": critical,
            "detection_rate": round(detected / total * 100, 1) if total else 0.0,
            "avg_confidence": round(avg_confidence or 0.0, 3),
            "avg_affected_area": round(avg_area or 0.0, 2),
            "severity_distribution": {r["severity"]: r["cnt"] for r in sev_rows},
            "inspection_timeline": [
                {"date": r["day"], "count": r["cnt"]} for r in timeline_rows
            ],
        }


# ── Singleton ──────────────────────────────────────────────────────────────

_repo: InspectionRepository | None = None


def get_repository() -> InspectionRepository:
    global _repo
    if _repo is None:
        init_db()
        _repo = InspectionRepository()
    return _repo
