"""
Database router — returns the right repository based on configuration.

The rest of the application imports only this module and calls get_repository().
It never imports sqlite_db or mongo_db directly.
"""

from __future__ import annotations

from typing import Any

from app.config import get_settings


def get_repository():
    """Return the appropriate repository based on MONGODB_URI setting."""
    settings = get_settings()
    if settings.mongodb_uri:
        from app.database.mongo_db import get_mongo_repository
        return get_mongo_repository()
    from app.database.sqlite_db import get_repository as get_sqlite_repo
    return get_sqlite_repo()
