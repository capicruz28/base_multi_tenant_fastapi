"""Cálculo determinista de scope_fingerprint (F16 TD-M-01)."""

from __future__ import annotations

import hashlib
from uuid import UUID

from app.core.codigo.enums import ScopeType

_NULL_UUID = "00000000-0000-0000-0000-000000000000"


def compute_scope_fingerprint(
    scope_type: ScopeType,
    *,
    empresa_id: UUID | None = None,
    almacen_id: UUID | None = None,
    punto_venta_id: UUID | None = None,
    serie_id: UUID | None = None,
) -> str:
    """Hash SHA-256 de dimensiones de scope con sentinels para NULL."""
    if scope_type == ScopeType.SERIE_FISCAL:
        parts = [
            scope_type.value,
            str(empresa_id) if empresa_id else _NULL_UUID,
            str(serie_id) if serie_id else _NULL_UUID,
            _NULL_UUID,
            _NULL_UUID,
        ]
    else:
        parts = [
            scope_type.value,
            str(empresa_id) if empresa_id else _NULL_UUID,
            str(almacen_id) if almacen_id else _NULL_UUID,
            str(punto_venta_id) if punto_venta_id else _NULL_UUID,
        ]
    payload = "|".join(parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
