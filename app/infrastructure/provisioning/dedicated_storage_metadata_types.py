"""Contratos internos — DedicatedStorageMetadataService (PR-F4-09)."""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class DedicatedStorageMetadataRequest:
    """Entrada S8 — registro metadata CP ``cliente_conexion``."""

    cliente_id: UUID
    provisioning_run_id: UUID
    servidor: str
    database_name: str
    app_login_name: str
    app_login_password: str
    puerto: int = 1433


@dataclass(frozen=True, slots=True)
class DedicatedStorageMetadataResult:
    """Resultado S8 — idempotente por conexión principal activa."""

    conexion_id: UUID
    created: bool
    idempotent: bool = False


__all__ = [
    "DedicatedStorageMetadataRequest",
    "DedicatedStorageMetadataResult",
]
