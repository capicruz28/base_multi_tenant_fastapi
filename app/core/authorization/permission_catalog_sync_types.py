"""Tipos compartidos — permission catalog sync (F12-B)."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Protocol


class SyncMode(str, Enum):
    CONTROL_PLANE = "control_plane"
    DEDICATED_DATA_PLANE = "dedicated_data_plane"


@dataclass(frozen=True, slots=True)
class SyncResult:
    inserted: int = 0
    updated: int = 0
    deactivated: int = 0
    declared_count: int = 0


class PermissionCatalogExecutor(Protocol):
    async def fetch_existing(self) -> list[dict]:
        ...

    async def resolve_modulo_id(self, modulo_codigo: str) -> Optional[str]:
        ...

    async def insert_permiso(
        self,
        *,
        permiso_id: str,
        codigo: str,
        nombre: str,
        descripcion: Optional[str],
        modulo_id: Optional[str],
        recurso: str,
        accion: str,
    ) -> None:
        ...

    async def update_permiso(
        self,
        *,
        codigo: str,
        nombre: str,
        descripcion: Optional[str],
        modulo_id: Optional[str],
        recurso: str,
        accion: str,
    ) -> None:
        ...

    async def deactivate_permiso(self, codigo: str) -> None:
        ...


__all__ = [
    "PermissionCatalogExecutor",
    "SyncMode",
    "SyncResult",
]
