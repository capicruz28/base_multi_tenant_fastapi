# app/modules/bdg/presentation/schemas.py
"""Schemas Pydantic para el módulo BDG (Presupuestos). Create/Update no incluyen cliente_id."""
from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


# ========== Presupuesto (cabecera) ==========
# API usa "anio"; BD usa "año". porcentaje_ejecucion se calcula en servicio.
class PresupuestoCreate(BaseModel):
    empresa_id: UUID
    codigo_presupuesto: str = Field(..., max_length=20)
    nombre: str = Field(..., max_length=100)
    anio: int = Field(..., ge=2000, le=2100)
    tipo_presupuesto: Optional[str] = Field("anual", max_length=20)
    monto_total_presupuestado: Optional[Decimal] = Field(0, ge=0)
    monto_total_ejecutado: Optional[Decimal] = Field(0, ge=0)
    estado: Optional[str] = Field("borrador", max_length=20)
    fecha_aprobacion: Optional[datetime] = None
    observaciones: Optional[str] = None
    usuario_creacion_id: Optional[UUID] = None


class PresupuestoUpdate(BaseModel):
    codigo_presupuesto: Optional[str] = None
    nombre: Optional[str] = None
    tipo_presupuesto: Optional[str] = None
    monto_total_presupuestado: Optional[Decimal] = None
    monto_total_ejecutado: Optional[Decimal] = None
    estado: Optional[str] = None
    fecha_aprobacion: Optional[datetime] = None
    observaciones: Optional[str] = None


class PresupuestoRead(BaseModel):
    presupuesto_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    codigo_presupuesto: str
    nombre: str
    anio: int
    tipo_presupuesto: Optional[str]
    monto_total_presupuestado: Optional[Decimal]
    monto_total_ejecutado: Optional[Decimal]
    porcentaje_ejecucion: Optional[Decimal] = None
    estado: Optional[str]
    fecha_aprobacion: Optional[datetime]
    observaciones: Optional[str]
    fecha_creacion: datetime
    usuario_creacion_id: Optional[UUID]

    class Config:
        from_attributes = True


# ========== Presupuesto Detalle ==========
# monto_disponible se calcula en servicio (monto_presupuestado - monto_ejecutado)
class PresupuestoDetalleCreate(BaseModel):
    presupuesto_id: UUID
    cuenta_id: UUID
    centro_costo_id: Optional[UUID] = None
    mes: Optional[int] = Field(None, ge=1, le=12)
    monto_presupuestado: Decimal = Field(..., ge=0)
    monto_ejecutado: Optional[Decimal] = Field(0, ge=0)
    observaciones: Optional[str] = None


class PresupuestoDetalleUpdate(BaseModel):
    cuenta_id: Optional[UUID] = None
    centro_costo_id: Optional[UUID] = None
    mes: Optional[int] = None
    monto_presupuestado: Optional[Decimal] = None
    monto_ejecutado: Optional[Decimal] = None
    observaciones: Optional[str] = None


class PresupuestoDetalleRead(BaseModel):
    presupuesto_detalle_id: UUID
    cliente_id: UUID
    presupuesto_id: UUID
    cuenta_id: UUID
    centro_costo_id: Optional[UUID]
    mes: Optional[int]
    monto_presupuestado: Decimal
    monto_ejecutado: Optional[Decimal]
    monto_disponible: Optional[Decimal] = None
    observaciones: Optional[str]
    fecha_creacion: datetime

    class Config:
        from_attributes = True
