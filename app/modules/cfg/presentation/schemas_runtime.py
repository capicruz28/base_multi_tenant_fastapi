"""Schemas REST — Runtime Snapshot (solo lectura).

Separados de ``schemas.py`` (CFG Admin). No reutilizar CodigoSecuenciaRead.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CodigoRuntimeSequenceResponse(BaseModel):
    """Ítem Runtime Snapshot — contrato HTTP v1.0."""

    model_config = ConfigDict(from_attributes=True)

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


class CodigoRuntimeSnapshotResponse(BaseModel):
    """Documento Runtime Snapshot — GET /cfg/runtime/snapshot."""

    model_config = ConfigDict(from_attributes=True)

    schema_version: str
    generated_at: datetime
    content_revision: str
    items: list[CodigoRuntimeSequenceResponse] = Field(default_factory=list)


__all__ = [
    "CodigoRuntimeSequenceResponse",
    "CodigoRuntimeSnapshotResponse",
]
