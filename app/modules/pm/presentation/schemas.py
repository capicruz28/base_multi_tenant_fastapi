# app/modules/pm/presentation/schemas.py
"""Schemas Pydantic para el modulo PM (Gestion de Proyectos). Create/Update no incluyen cliente_id."""
from typing import Optional
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field


# ========== Proyecto ==========
class ProyectoCreate(BaseModel):
    empresa_id: UUID
    codigo_proyecto: str = Field(..., max_length=20)
    nombre: str = Field(..., max_length=150)
    descripcion: Optional[str] = None
    cliente_venta_id: Optional[UUID] = None
    fecha_inicio: date
    fecha_fin_estimada: Optional[date] = None
    fecha_fin_real: Optional[date] = None
    presupuesto: Optional[Decimal] = None
    costo_real: Optional[Decimal] = Field(0, ge=0)
    responsable_usuario_id: Optional[UUID] = None
    estado: Optional[str] = Field("planificado", max_length=20)


class ProyectoUpdate(BaseModel):
    codigo_proyecto: Optional[str] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    cliente_venta_id: Optional[UUID] = None
    fecha_inicio: Optional[date] = None
    fecha_fin_estimada: Optional[date] = None
    fecha_fin_real: Optional[date] = None
    presupuesto: Optional[Decimal] = None
    costo_real: Optional[Decimal] = None
    responsable_usuario_id: Optional[UUID] = None
    estado: Optional[str] = None


class ProyectoRead(BaseModel):
    proyecto_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    codigo_proyecto: str
    nombre: str
    descripcion: Optional[str]
    cliente_venta_id: Optional[UUID]
    fecha_inicio: date
    fecha_fin_estimada: Optional[date]
    fecha_fin_real: Optional[date]
    presupuesto: Optional[Decimal]
    costo_real: Optional[Decimal]
    responsable_usuario_id: Optional[UUID]
    estado: Optional[str]
    fecha_creacion: datetime

    class Config:
        from_attributes = True
