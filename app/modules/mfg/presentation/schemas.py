# app/modules/mfg/presentation/schemas.py
"""Schemas Pydantic para el módulo MFG (Manufactura). Create/Update no incluyen cliente_id."""
from typing import Optional
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field


# ========== Centro de Trabajo ==========
class CentroTrabajoCreate(BaseModel):
    empresa_id: UUID
    codigo: str = Field(..., max_length=20)
    nombre: str = Field(..., max_length=100)
    descripcion: Optional[str] = None
    sucursal_id: Optional[UUID] = None
    ubicacion_fisica: Optional[str] = None
    tipo_centro: str = Field(..., max_length=30)
    capacidad_horas_dia: Optional[Decimal] = None
    capacidad_unidades_hora: Optional[Decimal] = None
    eficiencia_promedio: Optional[Decimal] = Field(85, ge=0, le=100)
    costo_hora_maquina: Optional[Decimal] = None
    costo_setup: Optional[Decimal] = None
    centro_costo_id: Optional[UUID] = None
    requiere_mantenimiento: Optional[bool] = True
    frecuencia_mantenimiento_dias: Optional[int] = None
    ultima_fecha_mantenimiento: Optional[date] = None
    estado_centro: Optional[str] = Field("disponible", max_length=20)
    es_activo: Optional[bool] = True


class CentroTrabajoUpdate(BaseModel):
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    sucursal_id: Optional[UUID] = None
    ubicacion_fisica: Optional[str] = None
    tipo_centro: Optional[str] = None
    capacidad_horas_dia: Optional[Decimal] = None
    capacidad_unidades_hora: Optional[Decimal] = None
    eficiencia_promedio: Optional[Decimal] = None
    costo_hora_maquina: Optional[Decimal] = None
    costo_setup: Optional[Decimal] = None
    centro_costo_id: Optional[UUID] = None
    requiere_mantenimiento: Optional[bool] = None
    frecuencia_mantenimiento_dias: Optional[int] = None
    ultima_fecha_mantenimiento: Optional[date] = None
    estado_centro: Optional[str] = None
    es_activo: Optional[bool] = None


class CentroTrabajoRead(BaseModel):
    centro_trabajo_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    codigo: str
    nombre: str
    descripcion: Optional[str]
    sucursal_id: Optional[UUID]
    ubicacion_fisica: Optional[str]
    tipo_centro: Optional[str]
    capacidad_horas_dia: Optional[Decimal]
    capacidad_unidades_hora: Optional[Decimal]
    eficiencia_promedio: Optional[Decimal]
    costo_hora_maquina: Optional[Decimal]
    costo_setup: Optional[Decimal]
    centro_costo_id: Optional[UUID]
    requiere_mantenimiento: Optional[bool]
    frecuencia_mantenimiento_dias: Optional[int]
    ultima_fecha_mantenimiento: Optional[date]
    estado_centro: Optional[str]
    es_activo: Optional[bool]
    fecha_creacion: datetime
    usuario_creacion_id: Optional[UUID]
    class Config:
        from_attributes = True


# ========== Operación ==========
class OperacionCreate(BaseModel):
    empresa_id: UUID
    codigo: str = Field(..., max_length=20)
    nombre: str = Field(..., max_length=100)
    descripcion: Optional[str] = None
    centro_trabajo_id: Optional[UUID] = None
    tiempo_setup_minutos: Optional[Decimal] = None
    tiempo_operacion_minutos: Optional[Decimal] = None
    requiere_herramientas: Optional[str] = None
    requiere_habilidad: Optional[str] = None
    requiere_inspeccion: Optional[bool] = False
    plan_inspeccion_id: Optional[UUID] = None
    es_activo: Optional[bool] = True


class OperacionUpdate(BaseModel):
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    centro_trabajo_id: Optional[UUID] = None
    tiempo_setup_minutos: Optional[Decimal] = None
    tiempo_operacion_minutos: Optional[Decimal] = None
    requiere_herramientas: Optional[str] = None
    requiere_habilidad: Optional[str] = None
    requiere_inspeccion: Optional[bool] = None
    plan_inspeccion_id: Optional[UUID] = None
    es_activo: Optional[bool] = None


class OperacionRead(BaseModel):
    operacion_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    codigo: str
    nombre: str
    descripcion: Optional[str]
    centro_trabajo_id: Optional[UUID]
    tiempo_setup_minutos: Optional[Decimal]
    tiempo_operacion_minutos: Optional[Decimal]
    requiere_herramientas: Optional[str]
    requiere_habilidad: Optional[str]
    requiere_inspeccion: Optional[bool]
    plan_inspeccion_id: Optional[UUID]
    es_activo: Optional[bool]
    fecha_creacion: datetime
    usuario_creacion_id: Optional[UUID]
    class Config:
        from_attributes = True


# ========== Lista de Materiales (BOM) ==========
class ListaMaterialesCreate(BaseModel):
    empresa_id: UUID
    codigo_bom: str = Field(..., max_length=20)
    producto_id: UUID
    version: Optional[str] = Field("1.0", max_length=10)
    fecha_vigencia_desde: date
    fecha_vigencia_hasta: Optional[date] = None
    cantidad_base: Optional[Decimal] = Field(1, ge=0)
    unidad_medida_id: UUID
    tipo_bom: Optional[str] = Field("produccion", max_length=20)
    porcentaje_desperdicio: Optional[Decimal] = Field(0, ge=0, le=100)
    es_bom_activa: Optional[bool] = True
    estado: Optional[str] = Field("borrador", max_length=20)
    aprobado_por_usuario_id: Optional[UUID] = None
    fecha_aprobacion: Optional[date] = None
    observaciones: Optional[str] = None


class ListaMaterialesUpdate(BaseModel):
    codigo_bom: Optional[str] = None
    producto_id: Optional[UUID] = None
    version: Optional[str] = None
    fecha_vigencia_desde: Optional[date] = None
    fecha_vigencia_hasta: Optional[date] = None
    cantidad_base: Optional[Decimal] = None
    unidad_medida_id: Optional[UUID] = None
    tipo_bom: Optional[str] = None
    porcentaje_desperdicio: Optional[Decimal] = None
    es_bom_activa: Optional[bool] = None
    estado: Optional[str] = None
    aprobado_por_usuario_id: Optional[UUID] = None
    fecha_aprobacion: Optional[date] = None
    observaciones: Optional[str] = None


class ListaMaterialesRead(BaseModel):
    bom_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    codigo_bom: str
    producto_id: UUID
    version: Optional[str]
    fecha_vigencia_desde: date
    fecha_vigencia_hasta: Optional[date]
    cantidad_base: Optional[Decimal]
    unidad_medida_id: UUID
    tipo_bom: Optional[str]
    porcentaje_desperdicio: Optional[Decimal]
    es_bom_activa: Optional[bool]
    estado: Optional[str]
    aprobado_por_usuario_id: Optional[UUID]
    fecha_aprobacion: Optional[date]
    observaciones: Optional[str]
    fecha_creacion: datetime
    usuario_creacion_id: Optional[UUID]
    class Config:
        from_attributes = True


# ========== BOM Detalle ==========
class ListaMaterialesDetalleCreate(BaseModel):
    bom_id: UUID
    producto_componente_id: UUID
    cantidad: Decimal = Field(..., gt=0)
    unidad_medida_id: UUID
    tipo_componente: Optional[str] = Field("material", max_length=20)
    es_critico: Optional[bool] = False
    porcentaje_desperdicio: Optional[Decimal] = Field(0, ge=0, le=100)
    tiene_sustitutos: Optional[bool] = False
    productos_sustitutos: Optional[str] = None
    secuencia: Optional[int] = 0
    observaciones: Optional[str] = None


class ListaMaterialesDetalleUpdate(BaseModel):
    producto_componente_id: Optional[UUID] = None
    cantidad: Optional[Decimal] = None
    unidad_medida_id: Optional[UUID] = None
    tipo_componente: Optional[str] = None
    es_critico: Optional[bool] = None
    porcentaje_desperdicio: Optional[Decimal] = None
    tiene_sustitutos: Optional[bool] = None
    productos_sustitutos: Optional[str] = None
    secuencia: Optional[int] = None
    observaciones: Optional[str] = None


class ListaMaterialesDetalleRead(BaseModel):
    bom_detalle_id: UUID
    cliente_id: UUID
    bom_id: UUID
    producto_componente_id: UUID
    cantidad: Decimal
    unidad_medida_id: UUID
    tipo_componente: Optional[str]
    es_critico: Optional[bool]
    porcentaje_desperdicio: Optional[Decimal]
    tiene_sustitutos: Optional[bool]
    productos_sustitutos: Optional[str]
    secuencia: Optional[int]
    observaciones: Optional[str]
    fecha_creacion: datetime
    class Config:
        from_attributes = True


# ========== Ruta de Fabricación ==========
class RutaFabricacionCreate(BaseModel):
    empresa_id: UUID
    codigo_ruta: str = Field(..., max_length=20)
    producto_id: UUID
    bom_id: Optional[UUID] = None
    nombre: str = Field(..., max_length=100)
    descripcion: Optional[str] = None
    version: Optional[str] = Field("1.0", max_length=10)
    tiempo_total_setup_minutos: Optional[Decimal] = Field(0, ge=0)
    tiempo_total_operacion_minutos: Optional[Decimal] = Field(0, ge=0)
    es_ruta_activa: Optional[bool] = True
    estado: Optional[str] = Field("borrador", max_length=20)


class RutaFabricacionUpdate(BaseModel):
    codigo_ruta: Optional[str] = None
    producto_id: Optional[UUID] = None
    bom_id: Optional[UUID] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    version: Optional[str] = None
    tiempo_total_setup_minutos: Optional[Decimal] = None
    tiempo_total_operacion_minutos: Optional[Decimal] = None
    es_ruta_activa: Optional[bool] = None
    estado: Optional[str] = None


class RutaFabricacionRead(BaseModel):
    ruta_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    codigo_ruta: str
    producto_id: UUID
    bom_id: Optional[UUID]
    nombre: str
    descripcion: Optional[str]
    version: Optional[str]
    tiempo_total_setup_minutos: Optional[Decimal]
    tiempo_total_operacion_minutos: Optional[Decimal]
    es_ruta_activa: Optional[bool]
    estado: Optional[str]
    fecha_creacion: datetime
    usuario_creacion_id: Optional[UUID]
    class Config:
        from_attributes = True


# ========== Ruta Fabricación Detalle ==========
class RutaFabricacionDetalleCreate(BaseModel):
    ruta_id: UUID
    secuencia: int = Field(..., ge=1)
    operacion_id: UUID
    centro_trabajo_id: UUID
    tiempo_setup_minutos: Optional[Decimal] = Field(0, ge=0)
    tiempo_operacion_minutos: Optional[Decimal] = Field(0, ge=0)
    es_operacion_critica: Optional[bool] = False
    permite_operaciones_paralelas: Optional[bool] = False
    instrucciones: Optional[str] = None


class RutaFabricacionDetalleUpdate(BaseModel):
    secuencia: Optional[int] = None
    operacion_id: Optional[UUID] = None
    centro_trabajo_id: Optional[UUID] = None
    tiempo_setup_minutos: Optional[Decimal] = None
    tiempo_operacion_minutos: Optional[Decimal] = None
    es_operacion_critica: Optional[bool] = None
    permite_operaciones_paralelas: Optional[bool] = None
    instrucciones: Optional[str] = None


class RutaFabricacionDetalleRead(BaseModel):
    ruta_detalle_id: UUID
    cliente_id: UUID
    ruta_id: UUID
    secuencia: int
    operacion_id: UUID
    centro_trabajo_id: UUID
    tiempo_setup_minutos: Optional[Decimal]
    tiempo_operacion_minutos: Optional[Decimal]
    es_operacion_critica: Optional[bool]
    permite_operaciones_paralelas: Optional[bool]
    instrucciones: Optional[str]
    fecha_creacion: datetime
    class Config:
        from_attributes = True


# ========== Orden de Producción ==========
class OrdenProduccionCreate(BaseModel):
    empresa_id: UUID
    numero_op: str = Field(..., max_length=20)
    fecha_emision: Optional[date] = None
    fecha_inicio_programada: date
    fecha_fin_programada: date
    producto_id: UUID
    bom_id: UUID
    ruta_fabricacion_id: Optional[UUID] = None
    cantidad_planeada: Decimal = Field(..., gt=0)
    cantidad_producida: Optional[Decimal] = Field(0, ge=0)
    cantidad_defectuosa: Optional[Decimal] = Field(0, ge=0)
    unidad_medida_id: UUID
    almacen_destino_id: Optional[UUID] = None
    prioridad: Optional[int] = Field(3, ge=1, le=4)
    tipo_orden: Optional[str] = Field("normal", max_length=20)
    documento_origen_tipo: Optional[str] = None
    documento_origen_id: Optional[UUID] = None
    costo_materiales: Optional[Decimal] = Field(0, ge=0)
    costo_mano_obra: Optional[Decimal] = Field(0, ge=0)
    costo_cif: Optional[Decimal] = Field(0, ge=0)
    moneda: Optional[str] = Field("PEN", max_length=3)
    centro_costo_id: Optional[UUID] = None
    estado: Optional[str] = Field("borrador", max_length=20)
    responsable_usuario_id: Optional[UUID] = None
    responsable_nombre: Optional[str] = None
    observaciones: Optional[str] = None


class OrdenProduccionUpdate(BaseModel):
    numero_op: Optional[str] = None
    fecha_inicio_programada: Optional[date] = None
    fecha_fin_programada: Optional[date] = None
    producto_id: Optional[UUID] = None
    bom_id: Optional[UUID] = None
    ruta_fabricacion_id: Optional[UUID] = None
    cantidad_planeada: Optional[Decimal] = None
    cantidad_producida: Optional[Decimal] = None
    cantidad_defectuosa: Optional[Decimal] = None
    unidad_medida_id: Optional[UUID] = None
    almacen_destino_id: Optional[UUID] = None
    prioridad: Optional[int] = None
    tipo_orden: Optional[str] = None
    documento_origen_tipo: Optional[str] = None
    documento_origen_id: Optional[UUID] = None
    fecha_inicio_real: Optional[datetime] = None
    fecha_fin_real: Optional[datetime] = None
    costo_materiales: Optional[Decimal] = None
    costo_mano_obra: Optional[Decimal] = None
    costo_cif: Optional[Decimal] = None
    centro_costo_id: Optional[UUID] = None
    estado: Optional[str] = None
    responsable_usuario_id: Optional[UUID] = None
    responsable_nombre: Optional[str] = None
    observaciones: Optional[str] = None


class OrdenProduccionRead(BaseModel):
    orden_produccion_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    numero_op: str
    fecha_emision: date
    fecha_inicio_programada: date
    fecha_fin_programada: date
    producto_id: UUID
    bom_id: UUID
    ruta_fabricacion_id: Optional[UUID]
    cantidad_planeada: Decimal
    cantidad_producida: Optional[Decimal]
    cantidad_defectuosa: Optional[Decimal]
    unidad_medida_id: UUID
    almacen_destino_id: Optional[UUID]
    prioridad: Optional[int]
    tipo_orden: Optional[str]
    documento_origen_tipo: Optional[str]
    documento_origen_id: Optional[UUID]
    fecha_inicio_real: Optional[datetime]
    fecha_fin_real: Optional[datetime]
    costo_materiales: Optional[Decimal]
    costo_mano_obra: Optional[Decimal]
    costo_cif: Optional[Decimal]
    moneda: Optional[str]
    centro_costo_id: Optional[UUID]
    estado: Optional[str]
    responsable_usuario_id: Optional[UUID]
    responsable_nombre: Optional[str]
    observaciones: Optional[str]
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime]
    usuario_creacion_id: Optional[UUID]
    class Config:
        from_attributes = True


# ========== Orden Producción Operación ==========
class OrdenProduccionOperacionCreate(BaseModel):
    orden_produccion_id: UUID
    ruta_detalle_id: Optional[UUID] = None
    operacion_id: UUID
    centro_trabajo_id: UUID
    secuencia: int = Field(..., ge=1)
    tiempo_setup_planificado_minutos: Optional[Decimal] = Field(0, ge=0)
    tiempo_operacion_planificado_minutos: Optional[Decimal] = Field(0, ge=0)
    tiempo_setup_real_minutos: Optional[Decimal] = Field(0, ge=0)
    tiempo_operacion_real_minutos: Optional[Decimal] = Field(0, ge=0)
    fecha_inicio_programada: Optional[datetime] = None
    fecha_fin_programada: Optional[datetime] = None
    fecha_inicio_real: Optional[datetime] = None
    fecha_fin_real: Optional[datetime] = None
    cantidad_procesada: Optional[Decimal] = Field(0, ge=0)
    cantidad_aprobada: Optional[Decimal] = Field(0, ge=0)
    cantidad_rechazada: Optional[Decimal] = Field(0, ge=0)
    operario_usuario_id: Optional[UUID] = None
    operario_nombre: Optional[str] = None
    estado: Optional[str] = Field("pendiente", max_length=20)
    observaciones: Optional[str] = None


class OrdenProduccionOperacionUpdate(BaseModel):
    ruta_detalle_id: Optional[UUID] = None
    operacion_id: Optional[UUID] = None
    centro_trabajo_id: Optional[UUID] = None
    secuencia: Optional[int] = None
    tiempo_setup_planificado_minutos: Optional[Decimal] = None
    tiempo_operacion_planificado_minutos: Optional[Decimal] = None
    tiempo_setup_real_minutos: Optional[Decimal] = None
    tiempo_operacion_real_minutos: Optional[Decimal] = None
    fecha_inicio_programada: Optional[datetime] = None
    fecha_fin_programada: Optional[datetime] = None
    fecha_inicio_real: Optional[datetime] = None
    fecha_fin_real: Optional[datetime] = None
    cantidad_procesada: Optional[Decimal] = None
    cantidad_aprobada: Optional[Decimal] = None
    cantidad_rechazada: Optional[Decimal] = None
    operario_usuario_id: Optional[UUID] = None
    operario_nombre: Optional[str] = None
    estado: Optional[str] = None
    observaciones: Optional[str] = None


class OrdenProduccionOperacionRead(BaseModel):
    op_operacion_id: UUID
    cliente_id: UUID
    orden_produccion_id: UUID
    ruta_detalle_id: Optional[UUID]
    operacion_id: UUID
    centro_trabajo_id: UUID
    secuencia: int
    tiempo_setup_planificado_minutos: Optional[Decimal]
    tiempo_operacion_planificado_minutos: Optional[Decimal]
    tiempo_setup_real_minutos: Optional[Decimal]
    tiempo_operacion_real_minutos: Optional[Decimal]
    fecha_inicio_programada: Optional[datetime]
    fecha_fin_programada: Optional[datetime]
    fecha_inicio_real: Optional[datetime]
    fecha_fin_real: Optional[datetime]
    cantidad_procesada: Optional[Decimal]
    cantidad_aprobada: Optional[Decimal]
    cantidad_rechazada: Optional[Decimal]
    operario_usuario_id: Optional[UUID]
    operario_nombre: Optional[str]
    estado: Optional[str]
    observaciones: Optional[str]
    fecha_creacion: datetime
    class Config:
        from_attributes = True


# ========== Consumo Materiales ==========
class ConsumoMaterialesCreate(BaseModel):
    orden_produccion_id: UUID
    producto_id: UUID
    cantidad_planificada: Decimal = Field(..., ge=0)
    cantidad_consumida: Decimal = Field(..., ge=0)
    unidad_medida_id: UUID
    lote: Optional[str] = None
    almacen_origen_id: Optional[UUID] = None
    costo_unitario: Optional[Decimal] = Field(0, ge=0)
    movimiento_inventario_id: Optional[UUID] = None
    observaciones: Optional[str] = None


class ConsumoMaterialesUpdate(BaseModel):
    orden_produccion_id: Optional[UUID] = None
    producto_id: Optional[UUID] = None
    cantidad_planificada: Optional[Decimal] = None
    cantidad_consumida: Optional[Decimal] = None
    unidad_medida_id: Optional[UUID] = None
    lote: Optional[str] = None
    almacen_origen_id: Optional[UUID] = None
    costo_unitario: Optional[Decimal] = None
    movimiento_inventario_id: Optional[UUID] = None
    observaciones: Optional[str] = None


class ConsumoMaterialesRead(BaseModel):
    consumo_id: UUID
    cliente_id: UUID
    orden_produccion_id: UUID
    producto_id: UUID
    cantidad_planificada: Decimal
    cantidad_consumida: Decimal
    unidad_medida_id: UUID
    lote: Optional[str]
    almacen_origen_id: Optional[UUID]
    costo_unitario: Optional[Decimal]
    movimiento_inventario_id: Optional[UUID]
    observaciones: Optional[str]
    fecha_consumo: datetime
    usuario_registro_id: Optional[UUID]
    class Config:
        from_attributes = True
