"""Helpers for binding datetime values to SQL Server DATETIME columns."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional


def normalize_datetime_for_sql_server(value: Optional[datetime]) -> Optional[datetime]:
    """
    Convert timezone-aware datetimes to naive UTC for SQL Server DATETIME binding.

    pyodbc serializes aware datetimes with an offset suffix (+00:00), which SQL Server
    rejects with error 241 when the target column is DATETIME (not DATETIMEOFFSET).
    """
    if value is None:
        return None
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


def sql_int_or_zero(value: Any) -> int:
    """Coerce SQL aggregate results (possibly NULL) to int zero."""
    if value is None:
        return 0
    return int(value)
