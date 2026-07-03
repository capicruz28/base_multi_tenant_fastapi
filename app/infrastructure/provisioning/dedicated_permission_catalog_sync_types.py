"""Contratos internos — DedicatedPermissionCatalogSyncService (F12-B)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional
from uuid import UUID


@dataclass(frozen=True, slots=True)
class DedicatedPermissionCatalogSyncRequest:
    """Entrada S6b — sync PermissionRegistry → permiso en BD Dedicated."""

    database_name: str
    cliente_id: UUID
    provisioning_run_id: Optional[UUID] = None


@dataclass(frozen=True, slots=True)
class DedicatedPermissionCatalogSyncResult:
    """Resultado sync catálogo permisos DP — consumo interno saga S6."""

    database_name: str
    cliente_id: UUID
    status: str
    registry_hash: str
    inserted: int = 0
    updated: int = 0
    deactivated: int = 0
    declared_count: int = 0


__all__ = [
    "DedicatedPermissionCatalogSyncRequest",
    "DedicatedPermissionCatalogSyncResult",
]
