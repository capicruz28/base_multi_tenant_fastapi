"""Contratos internos — DedicatedCatalogSeedService (PR-F4-06)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass(frozen=True, slots=True)
class DedicatedCatalogSeedRequest:
    """Entrada S6 saga — seed catálogos en BD dedicada bootstrappeada."""

    database_name: str
    cliente_id: UUID
    plan_suscripcion: Optional[str] = None
    provisioning_run_id: Optional[UUID] = None


@dataclass(frozen=True, slots=True)
class CatalogRowVerification:
    """Resultado de verificación post-seed."""

    table_name: str
    row_count: int
    min_rows: int


@dataclass(frozen=True, slots=True)
class DedicatedCatalogSeedResult:
    """Resultado seed catálogos S6 — consumo interno saga F4-08."""

    database_name: str
    cliente_id: UUID
    plan_suscripcion: str
    profile_code: str
    scripts_executed: tuple[str, ...]
    scripts_skipped: tuple[str, ...]
    batches_executed: int
    row_verifications: tuple[CatalogRowVerification, ...]
    permission_catalog_sync_status: Optional[str] = None
    permission_catalog_sync_registry_hash: Optional[str] = None
    permission_catalog_sync_inserted: int = 0
    permission_catalog_sync_updated: int = 0
    permission_catalog_sync_deactivated: int = 0


__all__ = [
    "CatalogRowVerification",
    "DedicatedCatalogSeedRequest",
    "DedicatedCatalogSeedResult",
]
