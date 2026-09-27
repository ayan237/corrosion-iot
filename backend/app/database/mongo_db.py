"""
MongoDB database layer — used when MONGODB_URI is configured.

Wraps motor (async) but exposes the same synchronous-style interface as
sqlite_db.py so the rest of the application stays database-agnostic.

NOTE: Motor is async; we run it synchronously here via asyncio.get_event_loop()
so that the repository interface matches the SQLite version without requiring
async everywhere in the application.  In a production system you would make the
entire stack async; for this prototype the sync wrapper is acceptable.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import get_settings


def _run(coro):
    """Run a coroutine synchronously."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Inside an async context (e.g. pytest-asyncio) — use nest_asyncio or
            # fall back to a new thread.
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


class MongoInspectionRepository:
    def __init__(self):
        settings = get_settings()
        self._client = AsyncIOMotorClient(settings.mongodb_uri)
        self._db = self._client[settings.database_name]
        self._col = self._db["inspections"]

    # ── Internal helpers ──────────────────────────────────────────────────

    @staticmethod
    def _clean(doc: dict) -> dict:
        """Remove MongoDB _id field before returning to caller."""
        doc.pop("_id", None)
        return doc

    # ── Public interface (mirrors sqlite_db.InspectionRepository) ─────────

    def save(self, record: dict[str, Any]) -> dict[str, Any]:
        async def _save():
            await self._col.replace_one(
                {"inspection_id": record["inspection_id"]},
                record,
                upsert=True,
            )
        _run(_save())
        return record

    def get_by_id(self, inspection_id: str) -> dict[str, Any] | None:
        async def _get():
            return await self._col.find_one(
                {"inspection_id": inspection_id}, {"_id": 0}
            )
        return _run(_get())

    def list_inspections(
        self,
        page: int = 1,
        page_size: int = 20,
        severity: str | None = None,
        detected: bool | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> dict[str, Any]:
        query: dict[str, Any] = {}
        if severity:
            query["severity"] = severity
        if detected is not None:
            query["detected"] = detected
        if date_from or date_to:
            ts_filter: dict[str, Any] = {}
            if date_from:
                ts_filter["$gte"] = date_from
            if date_to:
                ts_filter["$lte"] = date_to
            query["timestamp"] = ts_filter

        async def _list():
            total = await self._col.count_documents(query)
            skip = (page - 1) * page_size
            cursor = (
                self._col.find(query, {"_id": 0})
                .sort("timestamp", -1)
                .skip(skip)
                .limit(page_size)
            )
            items = await cursor.to_list(length=page_size)
            return total, items

        total, items = _run(_list())
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": max(1, -(-total // page_size)),
        }

    def get_statistics(self) -> dict[str, Any]:
        async def _stats():
            total = await self._col.count_documents({})
            detected = await self._col.count_documents({"detected": True})
            high_critical = await self._col.count_documents(
                {"severity": {"$in": ["High", "Critical"]}}
            )
            critical = await self._col.count_documents({"severity": "Critical"})

            # Average confidence and area
            pipeline_avg = [
                {"$group": {
                    "_id": None,
                    "avg_confidence": {"$avg": "$confidence"},
                    "avg_area": {"$avg": "$affected_area"},
                }}
            ]
            avg_result = await self._col.aggregate(pipeline_avg).to_list(1)
            avg_conf = avg_result[0]["avg_confidence"] if avg_result else 0.0
            avg_area = avg_result[0]["avg_area"] if avg_result else 0.0

            # Severity distribution
            pipeline_sev = [
                {"$match": {"severity": {"$ne": None}}},
                {"$group": {"_id": "$severity", "count": {"$sum": 1}}},
            ]
            sev_result = await self._col.aggregate(pipeline_sev).to_list(10)
            sev_dist = {r["_id"]: r["count"] for r in sev_result}

            return {
                "total_inspections": total,
                "corrosion_detected": detected,
                "no_corrosion": total - detected,
                "high_critical_cases": high_critical,
                "critical_cases": critical,
                "detection_rate": round(detected / total * 100, 1) if total else 0.0,
                "avg_confidence": round(avg_conf or 0.0, 3),
                "avg_affected_area": round(avg_area or 0.0, 2),
                "severity_distribution": sev_dist,
                "inspection_timeline": [],  # simplified for Mongo version
            }

        return _run(_stats())


_repo: MongoInspectionRepository | None = None


def get_mongo_repository() -> MongoInspectionRepository:
    global _repo
    if _repo is None:
        _repo = MongoInspectionRepository()
    return _repo
