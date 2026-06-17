"""
Schemas auxiliares para acciones de proceso (INV).
"""
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, field_validator

from app.shared.validators import normalize_strip


class _MotivoAnulacionWriteMixin:
    @field_validator("motivo", mode="before")
    @classmethod
    def _strip_motivo(cls, v: Optional[str]) -> Optional[str]:
        return normalize_strip(v)


class _AprobarInventarioFisicoWriteMixin:
    @field_validator("observaciones", mode="before")
    @classmethod
    def _strip_observaciones(cls, v: Optional[str]) -> Optional[str]:
        return normalize_strip(v)


class MotivoAnulacion(_MotivoAnulacionWriteMixin, BaseModel):
    motivo: Optional[str] = Field(None, max_length=500)


class MotivoEstorno(_MotivoAnulacionWriteMixin, BaseModel):
    motivo: Optional[str] = Field(None, max_length=500)


class AprobarInventarioFisicoRequest(_AprobarInventarioFisicoWriteMixin, BaseModel):
    tipo_movimiento_id: UUID = Field(..., description="Tipo de movimiento (clase: ajuste)")
    observaciones: Optional[str] = Field(None, max_length=500)

