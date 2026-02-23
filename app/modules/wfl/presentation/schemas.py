# app/modules/wfl/presentation/schemas.py
from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class FlujoTrabajoCreate(BaseModel):
    empresa_id: UUID
    codigo_flujo: str = Field(..., max_length=20)
    nombre: str = Field(..., max_length=150)
    descripcion: Optional[str] = Field(None, max_length=500)
    tipo_flujo: str = Field(..., max_length=30)
    modulo_aplicable: Optional[str] = Field(None, max_length=10)
    definicion_pasos: Optional[str] = None
    es_activo: Optional[bool] = True


class FlujoTrabajoUpdate(BaseModel):
    codigo_flujo: Optional[str] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    tipo_flujo: Optional[str] = None
    modulo_aplicable: Optional[str] = None
    definicion_pasos: Optional[str] = None
    es_activo: Optional[bool] = None


class FlujoTrabajoRead(BaseModel):
    flujo_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    codigo_flujo: str
    nombre: str
    descripcion: Optional[str]
    tipo_flujo: str
    modulo_aplicable: Optional[str]
    definicion_pasos: Optional[str]
    es_activo: Optional[bool]
    fecha_creacion: datetime

    class Config:
        from_attributes = True
