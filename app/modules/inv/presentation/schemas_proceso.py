"""
Schemas auxiliares para acciones de proceso (INV).
"""
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class MotivoAnulacion(BaseModel):
    motivo: Optional[str] = Field(None, max_length=500)


class AprobarInventarioFisicoRequest(BaseModel):
    tipo_movimiento_id: UUID = Field(..., description="Tipo de movimiento (clase: ajuste)")
    observaciones: Optional[str] = Field(None, max_length=500)

