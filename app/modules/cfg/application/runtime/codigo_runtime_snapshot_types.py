"""DTOs internos — Runtime Snapshot de códigos (contrato v1.0).

Independientes de CFG Admin (`CodigoSecuenciaRead`).
No son schemas HTTP / OpenAPI.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass(frozen=True, slots=True)
class CodigoRuntimeSequence:
    """Ítem proyectado de una fila cfg ∩ catálogo ∩ módulo activo."""

    sequence_key: str
    modulo_codigo: str
    scope_type: str
    generation_policy: str
    es_activo: bool
    prefijo: str
    separador: str
    longitud_numero: int
    supports_preview: bool
    allow_manual: bool
    normalize_case: str
    max_output_length: int
    empresa_id: Optional[UUID] = None
    almacen_id: Optional[UUID] = None
    punto_venta_id: Optional[UUID] = None


@dataclass(frozen=True, slots=True)
class CodigoRuntimeSnapshot:
    """Proyección puntual read-only del tenant (Runtime Snapshot v1.0)."""

    schema_version: str
    generated_at: datetime
    content_revision: str
    items: tuple[CodigoRuntimeSequence, ...]


__all__ = [
    "CodigoRuntimeSequence",
    "CodigoRuntimeSnapshot",
]
