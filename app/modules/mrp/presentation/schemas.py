# app/modules/mrp/presentation/schemas.py
"""Schemas Pydantic para el módulo MRP (Planeamiento de Materiales). Create/Update no incluyen cliente_id."""
from typing import Optional
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field


# ========== Plan Maestro MRP ==========
class PlanMaestroCreate(BaseModel):
    empresa_id: UUID
    codigo_plan: str = Field(..., max_length=20)
    nombre: str = Field(..., max_length=100)
    descripcion: Optional[str] = None
    fecha_inicio: date
    fecha_fin: date
    tipo_periodo: Optional[str] = Field("semanal", max_length=20)
    horizonte_planificacion_dias: Optional[int] = 90
    punto_reorden_dias: Optional[int] = 15
    estado: Optional[str] = Field("borrador", max_length=20)
    observaciones: Optional[str] = None


class PlanMaestroUpdate(BaseModel):
    codigo_plan: Optional[str] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    tipo_periodo: Optional[str] = None
    horizonte_planificacion_dias: Optional[int] = None
    punto_reorden_dias: Optional[int] = None
    estado: Optional[str] = None
    fecha_calculo: Optional[datetime] = None
    fecha_aprobacion: Optional[datetime] = None
    total_productos_planificados: Optional[int] = None
    total_requisiciones_generadas: Optional[int] = None
    total_ordenes_sugeridas: Optional[int] = None
    observaciones: Optional[str] = None


class PlanMaestroRead(BaseModel):
    plan_maestro_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    codigo_plan: str
    nombre: str
    descripcion: Optional[str]
    fecha_inicio: date
    fecha_fin: date
    tipo_periodo: Optional[str]
    horizonte_planificacion_dias: Optional[int]
    punto_reorden_dias: Optional[int]
    estado: Optional[str]
    fecha_calculo: Optional[datetime]
    fecha_aprobacion: Optional[datetime]
    total_productos_planificados: Optional[int]
    total_requisiciones_generadas: Optional[int]
    total_ordenes_sugeridas: Optional[int]
    observaciones: Optional[str]
    fecha_creacion: datetime
    usuario_creacion_id: Optional[UUID]

    class Config:
        from_attributes = True


# ========== Necesidad Bruta ==========
class NecesidadBrutaCreate(BaseModel):
    plan_maestro_id: UUID
    producto_id: UUID
    fecha_requerida: date
    cantidad_requerida: Decimal = Field(..., gt=0)
    unidad_medida_id: UUID
    origen: str = Field(..., max_length=30)
    documento_origen_id: Optional[UUID] = None
    documento_origen_numero: Optional[str] = None
    prioridad: Optional[int] = 3


class NecesidadBrutaUpdate(BaseModel):
    plan_maestro_id: Optional[UUID] = None
    producto_id: Optional[UUID] = None
    fecha_requerida: Optional[date] = None
    cantidad_requerida: Optional[Decimal] = None
    unidad_medida_id: Optional[UUID] = None
    origen: Optional[str] = None
    documento_origen_id: Optional[UUID] = None
    documento_origen_numero: Optional[str] = None
    prioridad: Optional[int] = None


class NecesidadBrutaRead(BaseModel):
    necesidad_id: UUID
    cliente_id: UUID
    plan_maestro_id: UUID
    producto_id: UUID
    fecha_requerida: date
    cantidad_requerida: Decimal
    unidad_medida_id: UUID
    origen: Optional[str]
    documento_origen_id: Optional[UUID]
    documento_origen_numero: Optional[str]
    prioridad: Optional[int]
    fecha_creacion: datetime

    class Config:
        from_attributes = True


# ========== Explosión Materiales ==========
class ExplosionMaterialesCreate(BaseModel):
    plan_maestro_id: UUID
    producto_padre_id: UUID
    necesidad_padre_id: Optional[UUID] = None
    producto_componente_id: UUID
    bom_detalle_id: Optional[UUID] = None
    nivel_bom: Optional[int] = 1
    cantidad_necesaria: Decimal = Field(..., gt=0)
    unidad_medida_id: UUID
    fecha_requerida: date
    stock_actual: Optional[Decimal] = Field(0, ge=0)
    stock_reservado: Optional[Decimal] = Field(0, ge=0)
    stock_transito: Optional[Decimal] = Field(0, ge=0)


class ExplosionMaterialesUpdate(BaseModel):
    plan_maestro_id: Optional[UUID] = None
    producto_padre_id: Optional[UUID] = None
    necesidad_padre_id: Optional[UUID] = None
    producto_componente_id: Optional[UUID] = None
    bom_detalle_id: Optional[UUID] = None
    nivel_bom: Optional[int] = None
    cantidad_necesaria: Optional[Decimal] = None
    unidad_medida_id: Optional[UUID] = None
    fecha_requerida: Optional[date] = None
    stock_actual: Optional[Decimal] = None
    stock_reservado: Optional[Decimal] = None
    stock_transito: Optional[Decimal] = None


class ExplosionMaterialesRead(BaseModel):
    explosion_id: UUID
    cliente_id: UUID
    plan_maestro_id: UUID
    producto_padre_id: UUID
    necesidad_padre_id: Optional[UUID]
    producto_componente_id: UUID
    bom_detalle_id: Optional[UUID]
    nivel_bom: Optional[int]
    cantidad_necesaria: Decimal
    unidad_medida_id: UUID
    fecha_requerida: date
    stock_actual: Optional[Decimal]
    stock_reservado: Optional[Decimal]
    stock_transito: Optional[Decimal]
    stock_disponible: Optional[Decimal] = None
    cantidad_a_ordenar: Optional[Decimal] = None
    fecha_calculo: datetime

    class Config:
        from_attributes = True


# ========== Orden Sugerida ==========
class OrdenSugeridaCreate(BaseModel):
    plan_maestro_id: UUID
    producto_id: UUID
    tipo_orden: str = Field(..., max_length=20)
    cantidad_sugerida: Decimal = Field(..., gt=0)
    unidad_medida_id: UUID
    fecha_requerida: date
    fecha_orden_sugerida: date
    explosion_materiales_id: Optional[UUID] = None
    proveedor_sugerido_id: Optional[UUID] = None
    lead_time_dias: Optional[int] = None
    estado: Optional[str] = Field("sugerida", max_length=20)
    observaciones: Optional[str] = None


class OrdenSugeridaUpdate(BaseModel):
    plan_maestro_id: Optional[UUID] = None
    producto_id: Optional[UUID] = None
    tipo_orden: Optional[str] = None
    cantidad_sugerida: Optional[Decimal] = None
    unidad_medida_id: Optional[UUID] = None
    fecha_requerida: Optional[date] = None
    fecha_orden_sugerida: Optional[date] = None
    explosion_materiales_id: Optional[UUID] = None
    proveedor_sugerido_id: Optional[UUID] = None
    lead_time_dias: Optional[int] = None
    estado: Optional[str] = None
    documento_generado_tipo: Optional[str] = None
    documento_generado_id: Optional[UUID] = None
    fecha_conversion: Optional[datetime] = None
    observaciones: Optional[str] = None


class OrdenSugeridaRead(BaseModel):
    orden_sugerida_id: UUID
    cliente_id: UUID
    plan_maestro_id: UUID
    producto_id: UUID
    tipo_orden: str
    cantidad_sugerida: Decimal
    unidad_medida_id: UUID
    fecha_requerida: date
    fecha_orden_sugerida: date
    explosion_materiales_id: Optional[UUID]
    proveedor_sugerido_id: Optional[UUID]
    lead_time_dias: Optional[int]
    estado: Optional[str]
    documento_generado_tipo: Optional[str]
    documento_generado_id: Optional[UUID]
    fecha_conversion: Optional[datetime]
    observaciones: Optional[str]
    fecha_creacion: datetime

    class Config:
        from_attributes = True
