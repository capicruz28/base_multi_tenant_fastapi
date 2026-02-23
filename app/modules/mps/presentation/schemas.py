# app/modules/mps/presentation/schemas.py
"""Schemas Pydantic para el módulo MPS (Plan Maestro de Producción). Create/Update no incluyen cliente_id."""
from typing import Optional
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field


# ========== Pronóstico Demanda ==========
class PronosticoDemandaCreate(BaseModel):
    empresa_id: UUID
    producto_id: UUID
    anio: int = Field(..., ge=2000, le=2100)
    mes: int = Field(..., ge=1, le=12)
    semana: Optional[int] = None
    fecha_inicio: date
    fecha_fin: date
    cantidad_pronosticada: Decimal = Field(..., gt=0)
    unidad_medida_id: UUID
    metodo_pronostico: Optional[str] = Field(None, max_length=30)
    confiabilidad_porcentaje: Optional[Decimal] = Field(None, ge=0, le=100)
    cantidad_real: Optional[Decimal] = None
    observaciones: Optional[str] = None


class PronosticoDemandaUpdate(BaseModel):
    producto_id: Optional[UUID] = None
    anio: Optional[int] = None
    mes: Optional[int] = None
    semana: Optional[int] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    cantidad_pronosticada: Optional[Decimal] = None
    unidad_medida_id: Optional[UUID] = None
    metodo_pronostico: Optional[str] = None
    confiabilidad_porcentaje: Optional[Decimal] = None
    cantidad_real: Optional[Decimal] = None
    observaciones: Optional[str] = None


class PronosticoDemandaRead(BaseModel):
    pronostico_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    producto_id: UUID
    anio: int
    mes: int
    semana: Optional[int]
    fecha_inicio: date
    fecha_fin: date
    cantidad_pronosticada: Decimal
    unidad_medida_id: UUID
    metodo_pronostico: Optional[str]
    confiabilidad_porcentaje: Optional[Decimal]
    cantidad_real: Optional[Decimal]
    desviacion: Optional[Decimal] = None
    observaciones: Optional[str]
    fecha_creacion: datetime
    usuario_creacion_id: Optional[UUID]

    class Config:
        from_attributes = True


# ========== Plan Producción ==========
class PlanProduccionCreate(BaseModel):
    empresa_id: UUID
    codigo_plan: str = Field(..., max_length=20)
    nombre: str = Field(..., max_length=100)
    fecha_inicio: date
    fecha_fin: date
    estado: Optional[str] = Field("borrador", max_length=20)
    observaciones: Optional[str] = None


class PlanProduccionUpdate(BaseModel):
    codigo_plan: Optional[str] = None
    nombre: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    estado: Optional[str] = None
    fecha_aprobacion: Optional[datetime] = None
    aprobado_por_usuario_id: Optional[UUID] = None
    observaciones: Optional[str] = None


class PlanProduccionRead(BaseModel):
    plan_produccion_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    codigo_plan: str
    nombre: str
    fecha_inicio: date
    fecha_fin: date
    estado: Optional[str]
    fecha_aprobacion: Optional[datetime]
    aprobado_por_usuario_id: Optional[UUID]
    observaciones: Optional[str]
    fecha_creacion: datetime
    usuario_creacion_id: Optional[UUID]

    class Config:
        from_attributes = True


# ========== Plan Producción Detalle ==========
class PlanProduccionDetalleCreate(BaseModel):
    plan_produccion_id: UUID
    producto_id: UUID
    fecha_inicio: date
    fecha_fin: date
    pronostico_demanda: Optional[Decimal] = Field(0, ge=0)
    pedidos_firmes: Optional[Decimal] = Field(0, ge=0)
    stock_inicial: Optional[Decimal] = Field(0, ge=0)
    stock_seguridad: Optional[Decimal] = Field(0, ge=0)
    cantidad_planificada: Decimal = Field(..., ge=0)
    cantidad_producida: Optional[Decimal] = Field(0, ge=0)
    unidad_medida_id: UUID
    capacidad_disponible: Optional[Decimal] = None
    observaciones: Optional[str] = None


class PlanProduccionDetalleUpdate(BaseModel):
    plan_produccion_id: Optional[UUID] = None
    producto_id: Optional[UUID] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    pronostico_demanda: Optional[Decimal] = None
    pedidos_firmes: Optional[Decimal] = None
    stock_inicial: Optional[Decimal] = None
    stock_seguridad: Optional[Decimal] = None
    cantidad_planificada: Optional[Decimal] = None
    cantidad_producida: Optional[Decimal] = None
    unidad_medida_id: Optional[UUID] = None
    capacidad_disponible: Optional[Decimal] = None
    observaciones: Optional[str] = None


class PlanProduccionDetalleRead(BaseModel):
    plan_detalle_id: UUID
    cliente_id: UUID
    plan_produccion_id: UUID
    producto_id: UUID
    fecha_inicio: date
    fecha_fin: date
    pronostico_demanda: Optional[Decimal]
    pedidos_firmes: Optional[Decimal]
    stock_inicial: Optional[Decimal]
    stock_seguridad: Optional[Decimal]
    cantidad_planificada: Decimal
    cantidad_producida: Optional[Decimal]
    unidad_medida_id: UUID
    capacidad_disponible: Optional[Decimal]
    porcentaje_uso_capacidad: Optional[Decimal] = None
    observaciones: Optional[str]
    fecha_creacion: datetime

    class Config:
        from_attributes = True
