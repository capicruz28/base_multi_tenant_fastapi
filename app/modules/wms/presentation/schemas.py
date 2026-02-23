# app/modules/wms/presentation/schemas.py
"""
Schemas Pydantic para el módulo WMS (Warehouse Management System).
Todos los Create/Update excluyen cliente_id; se asigna desde contexto en backend.
✅ Campos esenciales incluidos desde el inicio.
"""
from typing import Optional
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field


# ============================================================================
# ZONA DE ALMACÉN
# ============================================================================
class ZonaAlmacenCreate(BaseModel):
    almacen_id: UUID
    codigo: str = Field(..., max_length=20)
    nombre: str = Field(..., max_length=100)
    descripcion: Optional[str] = Field(None, max_length=255)
    tipo_zona: str = Field(..., max_length=30)  # 'recepcion', 'almacenaje', 'picking', 'despacho', 'cuarentena', 'merma'
    temperatura_min: Optional[Decimal] = None
    temperatura_max: Optional[Decimal] = None
    requiere_control_temperatura: Optional[bool] = False
    capacidad_m3: Optional[Decimal] = Field(None, ge=0)
    capacidad_kg: Optional[Decimal] = Field(None, ge=0)
    es_activo: Optional[bool] = True


class ZonaAlmacenUpdate(BaseModel):
    codigo: Optional[str] = Field(None, max_length=20)
    nombre: Optional[str] = Field(None, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=255)
    tipo_zona: Optional[str] = Field(None, max_length=30)
    temperatura_min: Optional[Decimal] = None
    temperatura_max: Optional[Decimal] = None
    requiere_control_temperatura: Optional[bool] = None
    capacidad_m3: Optional[Decimal] = Field(None, ge=0)
    capacidad_kg: Optional[Decimal] = Field(None, ge=0)
    es_activo: Optional[bool] = None


class ZonaAlmacenRead(BaseModel):
    zona_id: UUID
    cliente_id: UUID
    almacen_id: UUID
    codigo: str
    nombre: str
    descripcion: Optional[str]
    tipo_zona: str
    temperatura_min: Optional[Decimal]
    temperatura_max: Optional[Decimal]
    requiere_control_temperatura: Optional[bool]
    capacidad_m3: Optional[Decimal]
    capacidad_kg: Optional[Decimal]
    es_activo: bool
    fecha_creacion: datetime
    usuario_creacion_id: Optional[UUID]

    class Config:
        from_attributes = True


# ============================================================================
# UBICACIÓN
# ============================================================================
class UbicacionCreate(BaseModel):
    almacen_id: UUID
    zona_id: Optional[UUID] = None
    codigo_ubicacion: str = Field(..., max_length=30)
    pasillo: Optional[str] = Field(None, max_length=10)
    rack: Optional[str] = Field(None, max_length=10)
    nivel: Optional[int] = Field(None, ge=1)
    posicion: Optional[str] = Field(None, max_length=10)
    nombre: Optional[str] = Field(None, max_length=100)
    tipo_ubicacion: Optional[str] = Field("rack", max_length=30)
    capacidad_kg: Optional[Decimal] = Field(None, ge=0)
    capacidad_m3: Optional[Decimal] = Field(None, ge=0)
    capacidad_pallets: Optional[int] = Field(None, ge=0)
    alto_cm: Optional[Decimal] = Field(None, ge=0)
    ancho_cm: Optional[Decimal] = Field(None, ge=0)
    profundidad_cm: Optional[Decimal] = Field(None, ge=0)
    permite_multiples_productos: Optional[bool] = True
    permite_multiples_lotes: Optional[bool] = True
    es_ubicacion_picking: Optional[bool] = False
    estado_ubicacion: Optional[str] = Field("disponible", max_length=20)
    es_activo: Optional[bool] = True


class UbicacionUpdate(BaseModel):
    zona_id: Optional[UUID] = None
    codigo_ubicacion: Optional[str] = Field(None, max_length=30)
    pasillo: Optional[str] = Field(None, max_length=10)
    rack: Optional[str] = Field(None, max_length=10)
    nivel: Optional[int] = Field(None, ge=1)
    posicion: Optional[str] = Field(None, max_length=10)
    nombre: Optional[str] = Field(None, max_length=100)
    tipo_ubicacion: Optional[str] = Field(None, max_length=30)
    capacidad_kg: Optional[Decimal] = Field(None, ge=0)
    capacidad_m3: Optional[Decimal] = Field(None, ge=0)
    capacidad_pallets: Optional[int] = Field(None, ge=0)
    alto_cm: Optional[Decimal] = Field(None, ge=0)
    ancho_cm: Optional[Decimal] = Field(None, ge=0)
    profundidad_cm: Optional[Decimal] = Field(None, ge=0)
    permite_multiples_productos: Optional[bool] = None
    permite_multiples_lotes: Optional[bool] = None
    es_ubicacion_picking: Optional[bool] = None
    estado_ubicacion: Optional[str] = Field(None, max_length=20)
    es_activo: Optional[bool] = None


class UbicacionRead(BaseModel):
    ubicacion_id: UUID
    cliente_id: UUID
    almacen_id: UUID
    zona_id: Optional[UUID]
    codigo_ubicacion: str
    pasillo: Optional[str]
    rack: Optional[str]
    nivel: Optional[int]
    posicion: Optional[str]
    nombre: Optional[str]
    tipo_ubicacion: Optional[str]
    capacidad_kg: Optional[Decimal]
    capacidad_m3: Optional[Decimal]
    capacidad_pallets: Optional[int]
    alto_cm: Optional[Decimal]
    ancho_cm: Optional[Decimal]
    profundidad_cm: Optional[Decimal]
    permite_multiples_productos: Optional[bool]
    permite_multiples_lotes: Optional[bool]
    es_ubicacion_picking: Optional[bool]
    estado_ubicacion: Optional[str]
    es_activo: bool
    fecha_creacion: datetime
    usuario_creacion_id: Optional[UUID]

    class Config:
        from_attributes = True


# ============================================================================
# STOCK POR UBICACIÓN
# ============================================================================
class StockUbicacionCreate(BaseModel):
    almacen_id: UUID
    ubicacion_id: UUID
    producto_id: UUID
    cantidad: Decimal = Field(..., ge=0)
    unidad_medida_id: UUID
    lote: Optional[str] = Field(None, max_length=50)
    numero_serie: Optional[str] = Field(None, max_length=100)
    fecha_vencimiento: Optional[date] = None
    estado_stock: Optional[str] = Field("disponible", max_length=20)
    motivo_bloqueo: Optional[str] = Field(None, max_length=255)


class StockUbicacionUpdate(BaseModel):
    ubicacion_id: Optional[UUID] = None
    producto_id: Optional[UUID] = None
    cantidad: Optional[Decimal] = Field(None, ge=0)
    unidad_medida_id: Optional[UUID] = None
    lote: Optional[str] = Field(None, max_length=50)
    numero_serie: Optional[str] = Field(None, max_length=100)
    fecha_vencimiento: Optional[date] = None
    estado_stock: Optional[str] = Field(None, max_length=20)
    motivo_bloqueo: Optional[str] = Field(None, max_length=255)


class StockUbicacionRead(BaseModel):
    stock_ubicacion_id: UUID
    cliente_id: UUID
    almacen_id: UUID
    ubicacion_id: UUID
    producto_id: UUID
    cantidad: Decimal
    unidad_medida_id: UUID
    lote: Optional[str]
    numero_serie: Optional[str]
    fecha_vencimiento: Optional[date]
    estado_stock: Optional[str]
    motivo_bloqueo: Optional[str]
    fecha_ingreso: datetime
    fecha_actualizacion: Optional[datetime]

    class Config:
        from_attributes = True


# ============================================================================
# TAREA
# ============================================================================
class TareaCreate(BaseModel):
    almacen_id: UUID
    numero_tarea: str = Field(..., max_length=20)
    tipo_tarea: str = Field(..., max_length=30)  # 'picking', 'putaway', 'reabastecimiento', 'conteo', 'reubicacion'
    prioridad: Optional[int] = Field(3, ge=1, le=4)
    ubicacion_origen_id: Optional[UUID] = None
    ubicacion_destino_id: Optional[UUID] = None
    producto_id: Optional[UUID] = None
    cantidad_planeada: Optional[Decimal] = Field(None, ge=0)
    cantidad_completada: Optional[Decimal] = Field(0, ge=0)
    unidad_medida_id: Optional[UUID] = None
    documento_referencia_tipo: Optional[str] = Field(None, max_length=30)
    documento_referencia_id: Optional[UUID] = None
    asignado_usuario_id: Optional[UUID] = None
    asignado_nombre: Optional[str] = Field(None, max_length=150)
    estado: Optional[str] = Field("pendiente", max_length=20)
    instrucciones: Optional[str] = None
    observaciones: Optional[str] = Field(None, max_length=500)


class TareaUpdate(BaseModel):
    numero_tarea: Optional[str] = Field(None, max_length=20)
    tipo_tarea: Optional[str] = Field(None, max_length=30)
    prioridad: Optional[int] = Field(None, ge=1, le=4)
    ubicacion_origen_id: Optional[UUID] = None
    ubicacion_destino_id: Optional[UUID] = None
    producto_id: Optional[UUID] = None
    cantidad_planeada: Optional[Decimal] = Field(None, ge=0)
    cantidad_completada: Optional[Decimal] = Field(None, ge=0)
    unidad_medida_id: Optional[UUID] = None
    documento_referencia_tipo: Optional[str] = Field(None, max_length=30)
    documento_referencia_id: Optional[UUID] = None
    asignado_usuario_id: Optional[UUID] = None
    asignado_nombre: Optional[str] = Field(None, max_length=150)
    fecha_asignacion: Optional[datetime] = None
    estado: Optional[str] = Field(None, max_length=20)
    fecha_inicio: Optional[datetime] = None
    fecha_completado: Optional[datetime] = None
    instrucciones: Optional[str] = None
    observaciones: Optional[str] = Field(None, max_length=500)


class TareaRead(BaseModel):
    tarea_id: UUID
    cliente_id: UUID
    almacen_id: UUID
    numero_tarea: str
    tipo_tarea: str
    prioridad: Optional[int]
    ubicacion_origen_id: Optional[UUID]
    ubicacion_destino_id: Optional[UUID]
    producto_id: Optional[UUID]
    cantidad_planeada: Optional[Decimal]
    cantidad_completada: Optional[Decimal]
    unidad_medida_id: Optional[UUID]
    documento_referencia_tipo: Optional[str]
    documento_referencia_id: Optional[UUID]
    asignado_usuario_id: Optional[UUID]
    asignado_nombre: Optional[str]
    fecha_asignacion: Optional[datetime]
    estado: str
    fecha_inicio: Optional[datetime]
    fecha_completado: Optional[datetime]
    instrucciones: Optional[str]
    observaciones: Optional[str]
    fecha_creacion: datetime
    usuario_creacion_id: Optional[UUID]

    class Config:
        from_attributes = True
