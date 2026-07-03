"""Tipos compartidos — Product Reference Catalog Sync (F14)."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
from uuid import UUID


class SyncAction(str, Enum):
    INSERT = "insert"
    UPDATE = "update"
    SKIP = "skip"
    SOFT_DEACTIVATE = "soft_deactivate"


class CatalogSyncStatus(str, Enum):
    COMPLETED = "completed"
    FAILED = "failed"


class CatalogSyncBatchStatus(str, Enum):
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class SyncPlanEntry:
    action: SyncAction
    primary_key: str
    payload: Optional[dict[str, Any]] = None


@dataclass(frozen=True, slots=True)
class SyncPlan:
    catalog: str
    entries: tuple[SyncPlanEntry, ...] = ()


@dataclass(frozen=True, slots=True)
class CatalogSyncCounts:
    inserted: int = 0
    updated: int = 0
    skipped: int = 0
    deactivated: int = 0
    platform_total: int = 0
    dedicated_before: int = 0


@dataclass(frozen=True, slots=True)
class CatalogSyncErrorDetail:
    internal_code: str
    message: str
    details: Optional[dict[str, Any]] = None


@dataclass(frozen=True, slots=True)
class CatalogSyncResult:
    catalog: str
    cliente_id: UUID
    database_name: str
    status: CatalogSyncStatus
    codigo_cliente: str = ""
    razon_social: str = ""
    counts: Optional[CatalogSyncCounts] = None
    duration_ms: int = 0
    error: Optional[CatalogSyncErrorDetail] = None


@dataclass(frozen=True, slots=True)
class DedicatedTenantTarget:
    cliente_id: UUID
    codigo_cliente: str
    database_name: str
    razon_social: str = ""


@dataclass(frozen=True, slots=True)
class CatalogSyncTenantOutcome:
    cliente_id: UUID
    codigo_cliente: str
    database_name: str
    status: CatalogSyncStatus
    razon_social: str = ""
    counts: Optional[CatalogSyncCounts] = None
    duration_ms: int = 0
    error: Optional[CatalogSyncErrorDetail] = None


@dataclass(frozen=True, slots=True)
class CatalogSyncBatchResult:
    catalog: str
    status: CatalogSyncBatchStatus
    tenants_total: int = 0
    tenants_completed: int = 0
    tenants_failed: int = 0
    aggregated_counts: CatalogSyncCounts = field(default_factory=CatalogSyncCounts)
    outcomes: tuple[CatalogSyncTenantOutcome, ...] = ()
    duration_ms: int = 0


__all__ = [
    "CatalogSyncBatchResult",
    "CatalogSyncBatchStatus",
    "CatalogSyncCounts",
    "CatalogSyncErrorDetail",
    "CatalogSyncResult",
    "CatalogSyncStatus",
    "CatalogSyncTenantOutcome",
    "DedicatedTenantTarget",
    "SyncAction",
    "SyncPlan",
    "SyncPlanEntry",
]
