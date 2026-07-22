"""Contexto de generación de código (F16 `11` §6.1)."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.core.codigo.enums import GenerationOperation


@dataclass(slots=True)
class GenerationContext:
    client_id: UUID
    operation: GenerationOperation = GenerationOperation.CREATE
    empresa_id: UUID | None = None
    almacen_id: UUID | None = None
    punto_venta_id: UUID | None = None
    serie_id: UUID | None = None
    manual_code: str | None = None
    idempotency_key: str | None = None
