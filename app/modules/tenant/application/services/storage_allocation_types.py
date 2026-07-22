"""Contratos internos — StorageAllocationService (PR-F4-08 / H-04)."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from app.core.exceptions import ValidationError

_ALLOCATION_MARKER_VERSION = 1


@dataclass(frozen=True, slots=True)
class StorageAllocationRequest:
    cliente_id: UUID
    codigo_cliente: str
    subdominio: str


@dataclass(frozen=True, slots=True)
class StorageAllocationResult:
    servidor: str
    database_name: str
    app_login_name: str


def serialize_storage_allocation_marker(result: StorageAllocationResult) -> str:
    payload = {
        "v": _ALLOCATION_MARKER_VERSION,
        "servidor": result.servidor,
        "database_name": result.database_name,
        "app_login_name": result.app_login_name,
    }
    return json.dumps(payload, separators=(",", ":"), sort_keys=True)


def parse_storage_allocation_marker(marker: str) -> StorageAllocationResult:
    try:
        raw: dict[str, Any] = json.loads(marker)
    except json.JSONDecodeError as exc:
        raise ValidationError(
            detail="Marker storage_allocation inválido.",
            internal_code="STORAGE_ALLOCATION_MARKER_INVALID",
        ) from exc
    if raw.get("v") != _ALLOCATION_MARKER_VERSION:
        raise ValidationError(
            detail="Versión marker storage_allocation no soportada.",
            internal_code="STORAGE_ALLOCATION_MARKER_UNSUPPORTED",
        )
    try:
        return StorageAllocationResult(
            servidor=str(raw["servidor"]),
            database_name=str(raw["database_name"]),
            app_login_name=str(raw["app_login_name"]),
        )
    except KeyError as exc:
        raise ValidationError(
            detail="Marker storage_allocation incompleto.",
            internal_code="STORAGE_ALLOCATION_MARKER_INVALID",
        ) from exc


__all__ = [
    "StorageAllocationRequest",
    "StorageAllocationResult",
    "parse_storage_allocation_marker",
    "serialize_storage_allocation_marker",
]
