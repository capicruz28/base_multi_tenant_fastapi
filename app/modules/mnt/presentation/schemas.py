# app/modules/mnt/presentation/schemas.py
"""Schemas Pydantic para el módulo MNT (Mantenimiento). Create/Update no incluyen cliente_id."""
from typing import Optional
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field


# ========== Activo ==========
class ActivoCreate(BaseModel):
    empresa_id: UUID
    codigo_activo: str = Field(..., max_length=20)
    nombre: str = Field(..., max_length=150)
    descripcion: Optional[str] = None
    tipo_activo: str = Field(..., max_length=30)
    categoria: Optional[str] = None
    marca: Optional[str] = None
    modelo: Optional[str] = None
    numero_serie: Optional[str] = None
    anio_fabricacion: Optional[int] = Field(None, ge=1900, le=2100)
    sucursal_id: Optional[UUID] = None
    centro_trabajo_id: Optional[UUID] = None
    ubicacion_detalle: Optional[str] = None
    vehiculo_id: Optional[UUID] = None
    especificaciones_tecnicas: Optional[str] = None
    capacidad: Optional[str] = None
    potencia: Optional[str] = None
    fabricante: Optional[str] = None
    proveedor_id: Optional[UUID] = None
    fecha_adquisicion: Optional[date] = None
    fecha_puesta_operacion: Optional[date] = None
    vida_util_años: Optional[int] = None
    criticidad: Optional[str] = Field("media", max_length=20)
    valor_adquisicion: Optional[Decimal] = None
    valor_actual: Optional[Decimal] = None
    moneda: Optional[str] = Field("PEN", max_length=3)
    estado_activo: Optional[str] = Field("operativo", max_length=20)
    observaciones: Optional[str] = None
    es_activo: Optional[bool] = True


class ActivoUpdate(BaseModel):
    codigo_activo: Optional[str] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    tipo_activo: Optional[str] = None
    categoria: Optional[str] = None
    marca: Optional[str] = None
    modelo: Optional[str] = None
    numero_serie: Optional[str] = None
    anio_fabricacion: Optional[int] = None
    sucursal_id: Optional[UUID] = None
    centro_trabajo_id: Optional[UUID] = None
    ubicacion_detalle: Optional[str] = None
    vehiculo_id: Optional[UUID] = None
    especificaciones_tecnicas: Optional[str] = None
    capacidad: Optional[str] = None
    potencia: Optional[str] = None
    fabricante: Optional[str] = None
    proveedor_id: Optional[UUID] = None
    fecha_adquisicion: Optional[date] = None
    fecha_puesta_operacion: Optional[date] = None
    vida_util_años: Optional[int] = None
    criticidad: Optional[str] = None
    valor_adquisicion: Optional[Decimal] = None
    valor_actual: Optional[Decimal] = None
    moneda: Optional[str] = None
    estado_activo: Optional[str] = None
    observaciones: Optional[str] = None
    es_activo: Optional[bool] = None


class ActivoRead(BaseModel):
    activo_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    codigo_activo: str
    nombre: str
    descripcion: Optional[str]
    tipo_activo: Optional[str]
    categoria: Optional[str]
    marca: Optional[str]
    modelo: Optional[str]
    numero_serie: Optional[str]
    anio_fabricacion: Optional[int]
    sucursal_id: Optional[UUID]
    centro_trabajo_id: Optional[UUID]
    ubicacion_detalle: Optional[str]
    vehiculo_id: Optional[UUID]
    especificaciones_tecnicas: Optional[str]
    capacidad: Optional[str]
    potencia: Optional[str]
    fabricante: Optional[str]
    proveedor_id: Optional[UUID]
    fecha_adquisicion: Optional[date]
    fecha_puesta_operacion: Optional[date]
    vida_util_años: Optional[int]
    criticidad: Optional[str]
    valor_adquisicion: Optional[Decimal]
    valor_actual: Optional[Decimal]
    moneda: Optional[str]
    estado_activo: Optional[str]
    observaciones: Optional[str]
    es_activo: Optional[bool]
    fecha_creacion: datetime
    usuario_creacion_id: Optional[UUID]

    class Config:
        from_attributes = True


# ========== Plan Mantenimiento ==========
class PlanMantenimientoCreate(BaseModel):
    activo_id: UUID
    codigo_plan: str = Field(..., max_length=20)
    nombre: str = Field(..., max_length=100)
    descripcion: Optional[str] = None
    tipo_mantenimiento: str = Field(..., max_length=20)
    frecuencia_tipo: str = Field(..., max_length=20)
    frecuencia_valor: int = Field(..., gt=0)
    fecha_ultimo_mantenimiento: Optional[date] = None
    fecha_proximo_mantenimiento: Optional[date] = None
    horas_uso_ultimo: Optional[Decimal] = None
    horas_uso_proximo: Optional[Decimal] = None
    responsable_usuario_id: Optional[UUID] = None
    responsable_nombre: Optional[str] = None
    tareas_mantenimiento: Optional[str] = None
    costo_estimado: Optional[Decimal] = None
    moneda: Optional[str] = Field("PEN", max_length=3)
    es_activo: Optional[bool] = True


class PlanMantenimientoUpdate(BaseModel):
    activo_id: Optional[UUID] = None
    codigo_plan: Optional[str] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    tipo_mantenimiento: Optional[str] = None
    frecuencia_tipo: Optional[str] = None
    frecuencia_valor: Optional[int] = None
    fecha_ultimo_mantenimiento: Optional[date] = None
    fecha_proximo_mantenimiento: Optional[date] = None
    horas_uso_ultimo: Optional[Decimal] = None
    horas_uso_proximo: Optional[Decimal] = None
    responsable_usuario_id: Optional[UUID] = None
    responsable_nombre: Optional[str] = None
    tareas_mantenimiento: Optional[str] = None
    costo_estimado: Optional[Decimal] = None
    moneda: Optional[str] = None
    es_activo: Optional[bool] = None


class PlanMantenimientoRead(BaseModel):
    plan_mantenimiento_id: UUID
    cliente_id: UUID
    activo_id: UUID
    codigo_plan: str
    nombre: str
    descripcion: Optional[str]
    tipo_mantenimiento: Optional[str]
    frecuencia_tipo: Optional[str]
    frecuencia_valor: Optional[int]
    fecha_ultimo_mantenimiento: Optional[date]
    fecha_proximo_mantenimiento: Optional[date]
    horas_uso_ultimo: Optional[Decimal]
    horas_uso_proximo: Optional[Decimal]
    responsable_usuario_id: Optional[UUID]
    responsable_nombre: Optional[str]
    tareas_mantenimiento: Optional[str]
    costo_estimado: Optional[Decimal]
    moneda: Optional[str]
    es_activo: Optional[bool]
    fecha_creacion: datetime
    usuario_creacion_id: Optional[UUID]

    class Config:
        from_attributes = True


# ========== Orden Trabajo ==========
class OrdenTrabajoCreate(BaseModel):
    empresa_id: UUID
    numero_ot: str = Field(..., max_length=20)
    activo_id: UUID
    plan_mantenimiento_id: Optional[UUID] = None
    tipo_mantenimiento: str = Field(..., max_length=20)
    prioridad: Optional[str] = Field("media", max_length=20)
    problema_detectado: Optional[str] = None
    trabajo_a_realizar: str = Field(..., min_length=1)
    tecnico_asignado_usuario_id: Optional[UUID] = None
    tecnico_nombre: Optional[str] = None
    fecha_programada: Optional[datetime] = None
    fecha_inicio_real: Optional[datetime] = None
    fecha_fin_real: Optional[datetime] = None
    trabajo_realizado: Optional[str] = None
    repuestos_utilizados: Optional[str] = None
    costo_mano_obra: Optional[Decimal] = Field(0, ge=0)
    costo_repuestos: Optional[Decimal] = Field(0, ge=0)
    costo_servicios_terceros: Optional[Decimal] = Field(0, ge=0)
    moneda: Optional[str] = Field("PEN", max_length=3)
    estado: Optional[str] = Field("solicitada", max_length=20)
    fecha_cierre: Optional[datetime] = None
    cerrado_por_usuario_id: Optional[UUID] = None
    calificacion_trabajo: Optional[Decimal] = Field(None, ge=1, le=5)
    observaciones: Optional[str] = None


class OrdenTrabajoUpdate(BaseModel):
    numero_ot: Optional[str] = None
    activo_id: Optional[UUID] = None
    plan_mantenimiento_id: Optional[UUID] = None
    tipo_mantenimiento: Optional[str] = None
    prioridad: Optional[str] = None
    problema_detectado: Optional[str] = None
    trabajo_a_realizar: Optional[str] = None
    tecnico_asignado_usuario_id: Optional[UUID] = None
    tecnico_nombre: Optional[str] = None
    fecha_programada: Optional[datetime] = None
    fecha_inicio_real: Optional[datetime] = None
    fecha_fin_real: Optional[datetime] = None
    trabajo_realizado: Optional[str] = None
    repuestos_utilizados: Optional[str] = None
    costo_mano_obra: Optional[Decimal] = None
    costo_repuestos: Optional[Decimal] = None
    costo_servicios_terceros: Optional[Decimal] = None
    moneda: Optional[str] = None
    estado: Optional[str] = None
    fecha_cierre: Optional[datetime] = None
    cerrado_por_usuario_id: Optional[UUID] = None
    calificacion_trabajo: Optional[Decimal] = None
    observaciones: Optional[str] = None


class OrdenTrabajoRead(BaseModel):
    orden_trabajo_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    numero_ot: str
    fecha_solicitud: datetime
    activo_id: UUID
    plan_mantenimiento_id: Optional[UUID]
    tipo_mantenimiento: str
    prioridad: Optional[str]
    problema_detectado: Optional[str]
    trabajo_a_realizar: Optional[str]
    tecnico_asignado_usuario_id: Optional[UUID]
    tecnico_nombre: Optional[str]
    fecha_programada: Optional[datetime]
    fecha_inicio_real: Optional[datetime]
    fecha_fin_real: Optional[datetime]
    duracion_horas: Optional[Decimal] = None
    trabajo_realizado: Optional[str]
    repuestos_utilizados: Optional[str]
    costo_mano_obra: Optional[Decimal]
    costo_repuestos: Optional[Decimal]
    costo_servicios_terceros: Optional[Decimal]
    costo_total: Optional[Decimal] = None
    moneda: Optional[str]
    estado: Optional[str]
    fecha_cierre: Optional[datetime]
    cerrado_por_usuario_id: Optional[UUID]
    calificacion_trabajo: Optional[Decimal]
    observaciones: Optional[str]
    fecha_creacion: datetime
    usuario_creacion_id: Optional[UUID]

    class Config:
        from_attributes = True


# ========== Historial Mantenimiento ==========
class HistorialMantenimientoCreate(BaseModel):
    activo_id: UUID
    orden_trabajo_id: Optional[UUID] = None
    fecha_mantenimiento: date
    tipo_mantenimiento: str = Field(..., max_length=20)
    descripcion_trabajo: Optional[str] = None
    tecnico_nombre: Optional[str] = None
    horas_uso_activo: Optional[Decimal] = None
    kilometraje: Optional[Decimal] = None
    costo_total: Optional[Decimal] = Field(0, ge=0)
    moneda: Optional[str] = Field("PEN", max_length=3)
    observaciones: Optional[str] = None


class HistorialMantenimientoUpdate(BaseModel):
    activo_id: Optional[UUID] = None
    orden_trabajo_id: Optional[UUID] = None
    fecha_mantenimiento: Optional[date] = None
    tipo_mantenimiento: Optional[str] = None
    descripcion_trabajo: Optional[str] = None
    tecnico_nombre: Optional[str] = None
    horas_uso_activo: Optional[Decimal] = None
    kilometraje: Optional[Decimal] = None
    costo_total: Optional[Decimal] = None
    moneda: Optional[str] = None
    observaciones: Optional[str] = None


class HistorialMantenimientoRead(BaseModel):
    historial_id: UUID
    cliente_id: UUID
    activo_id: UUID
    orden_trabajo_id: Optional[UUID]
    fecha_mantenimiento: date
    tipo_mantenimiento: str
    descripcion_trabajo: Optional[str]
    tecnico_nombre: Optional[str]
    horas_uso_activo: Optional[Decimal]
    kilometraje: Optional[Decimal]
    costo_total: Optional[Decimal]
    moneda: Optional[str]
    observaciones: Optional[str]
    fecha_creacion: datetime

    class Config:
        from_attributes = True
