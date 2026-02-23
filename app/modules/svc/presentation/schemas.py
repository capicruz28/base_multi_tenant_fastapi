# app/modules/svc/presentation/schemas.py
"""Schemas Pydantic para el modulo SVC (Ordenes de Servicio). Create/Update no incluyen cliente_id."""
from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


# ========== Orden de Servicio ==========
class OrdenServicioCreate(BaseModel):
    empresa_id: UUID
    numero_os: str = Field(..., max_length=20)
    fecha_solicitud: Optional[datetime] = None
    cliente_venta_id: Optional[UUID] = None
    tipo_servicio: str = Field(..., max_length=50)
    descripcion_servicio: Optional[str] = None
    tecnico_asignado_usuario_id: Optional[UUID] = None
    fecha_inicio_programada: Optional[datetime] = None
    fecha_inicio_real: Optional[datetime] = None
    fecha_fin_real: Optional[datetime] = None
    estado: Optional[str] = Field("solicitada", max_length=20)
    monto_servicio: Optional[Decimal] = None


class OrdenServicioUpdate(BaseModel):
    numero_os: Optional[str] = None
    fecha_solicitud: Optional[datetime] = None
    cliente_venta_id: Optional[UUID] = None
    tipo_servicio: Optional[str] = None
    descripcion_servicio: Optional[str] = None
    tecnico_asignado_usuario_id: Optional[UUID] = None
    fecha_inicio_programada: Optional[datetime] = None
    fecha_inicio_real: Optional[datetime] = None
    fecha_fin_real: Optional[datetime] = None
    estado: Optional[str] = None
    monto_servicio: Optional[Decimal] = None


class OrdenServicioRead(BaseModel):
    orden_servicio_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    numero_os: str
    fecha_solicitud: datetime
    cliente_venta_id: Optional[UUID]
    tipo_servicio: str
    descripcion_servicio: Optional[str]
    tecnico_asignado_usuario_id: Optional[UUID]
    fecha_inicio_programada: Optional[datetime]
    fecha_inicio_real: Optional[datetime]
    fecha_fin_real: Optional[datetime]
    estado: Optional[str]
    monto_servicio: Optional[Decimal]
    fecha_creacion: datetime

    class Config:
        from_attributes = True
