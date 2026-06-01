"""
Dataclasses de resultado — OwnerSyncService v1.0.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID


@dataclass(frozen=True)
class OwnerSyncResult:
    cliente_id: UUID
    modulo_codigo: str
    admin_rol_id: UUID
    rol_permiso_inserted: int
    rol_permiso_total_module: int
    rol_menu_permiso_inserted: int
    rol_menu_permiso_total_module: int
    menu_codigos_sample: list[str] = field(default_factory=list)
    permiso_codigos_sample: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class OwnerSyncBatchResult:
    cliente_id: UUID
    results: list[OwnerSyncResult]

    @property
    def modulos_codigo(self) -> list[str]:
        return [r.modulo_codigo for r in self.results]

    @property
    def total_rol_menu_permiso_inserted(self) -> int:
        return sum(r.rol_menu_permiso_inserted for r in self.results)

    @property
    def total_rol_permiso_inserted(self) -> int:
        return sum(r.rol_permiso_inserted for r in self.results)


@dataclass(frozen=True)
class OwnerSyncDeactivateResult:
    cliente_id: UUID
    modulo_codigo: str
    runtime_only: bool = True
    cache_invalidated: bool = False
