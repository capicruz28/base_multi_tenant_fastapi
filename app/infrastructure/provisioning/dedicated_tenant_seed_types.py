"""Contratos internos — DedicatedTenantSeedService (PR-F4-07)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass(frozen=True, slots=True)
class DedicatedTenantSeedRequest:
    """Entrada S7 saga — seed tenant en BD dedicada (sin registry CP)."""

    database_name: str
    cliente_id: UUID
    codigo_cliente: str
    subdominio: str
    razon_social: str
    contacto_email: str
    plan_suscripcion: Optional[str] = None
    nombre_comercial: Optional[str] = None
    ruc: Optional[str] = None
    contacto_nombre: Optional[str] = None
    provisioning_run_id: Optional[UUID] = None
    admin_password: Optional[str] = None


@dataclass(frozen=True, slots=True)
class TenantSeedRowVerification:
    table_name: str
    row_count: int
    min_rows: int


@dataclass(frozen=True, slots=True)
class DedicatedTenantSeedResult:
    """Resultado seed tenant S7 — consumo interno saga F4-08."""

    database_name: str
    cliente_id: UUID
    plan_suscripcion: str
    profile_code: str
    admin_username: str
    admin_usuario_id: UUID
    admin_rol_id: UUID
    empresa_id: UUID
    steps_executed: tuple[str, ...]
    steps_skipped: tuple[str, ...]
    row_verifications: tuple[TenantSeedRowVerification, ...]


__all__ = [
    "DedicatedTenantSeedRequest",
    "DedicatedTenantSeedResult",
    "TenantSeedRowVerification",
]
