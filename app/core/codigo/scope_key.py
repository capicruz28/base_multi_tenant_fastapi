"""ScopeKey canónico para resolución de secuencias."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.core.codigo.enums import ScopeType
from app.core.codigo.scope_fingerprint import compute_scope_fingerprint


@dataclass(frozen=True, slots=True)
class ScopeKey:
    sequence_key: str
    scope_type: ScopeType
    client_id: UUID
    empresa_id: UUID | None = None
    almacen_id: UUID | None = None
    punto_venta_id: UUID | None = None
    serie_id: UUID | None = None

    @property
    def fingerprint(self) -> str:
        return compute_scope_fingerprint(
            self.scope_type,
            empresa_id=self.empresa_id,
            almacen_id=self.almacen_id,
            punto_venta_id=self.punto_venta_id,
            serie_id=self.serie_id,
        )
