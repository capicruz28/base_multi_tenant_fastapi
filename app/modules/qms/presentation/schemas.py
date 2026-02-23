# app/modules/qms/presentation/schemas.py
"""
Schemas Pydantic para el módulo QMS (Quality Management System).
Todos los Create/Update excluyen cliente_id; se asigna desde contexto en backend.
✅ Campos esenciales incluidos desde el inicio.
"""
from typing import Optional
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field


# ============================================================================
# PARÁMETRO DE CALIDAD
# ============================================================================
class ParametroCalidadCreate(BaseModel):
    empresa_id: UUID
    codigo: str = Field(..., max_length=20)
    nombre: str = Field(..., max_length=100)
    descripcion: Optional[str] = Field(None, max_length=255)
    tipo_parametro: str = Field(..., max_length=30)  # 'cuantitativo', 'cualitativo', 'pasa_no_pasa'
    unidad_medida_id: Optional[UUID] = None
    valor_minimo: Optional[Decimal] = None
    valor_maximo: Optional[Decimal] = None
    valor_objetivo: Optional[Decimal] = None
    opciones_permitidas: Optional[str] = None  # JSON string
    metodo_inspeccion: Optional[str] = Field(None, max_length=255)
    requiere_equipo: Optional[str] = Field(None, max_length=100)
    es_activo: Optional[bool] = True


class ParametroCalidadUpdate(BaseModel):
    codigo: Optional[str] = Field(None, max_length=20)
    nombre: Optional[str] = Field(None, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=255)
    tipo_parametro: Optional[str] = Field(None, max_length=30)
    unidad_medida_id: Optional[UUID] = None
    valor_minimo: Optional[Decimal] = None
    valor_maximo: Optional[Decimal] = None
    valor_objetivo: Optional[Decimal] = None
    opciones_permitidas: Optional[str] = None
    metodo_inspeccion: Optional[str] = Field(None, max_length=255)
    requiere_equipo: Optional[str] = Field(None, max_length=100)
    es_activo: Optional[bool] = None


class ParametroCalidadRead(BaseModel):
    parametro_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    codigo: str
    nombre: str
    descripcion: Optional[str]
    tipo_parametro: str
    unidad_medida_id: Optional[UUID]
    valor_minimo: Optional[Decimal]
    valor_maximo: Optional[Decimal]
    valor_objetivo: Optional[Decimal]
    opciones_permitidas: Optional[str]
    metodo_inspeccion: Optional[str]
    requiere_equipo: Optional[str]
    es_activo: bool
    fecha_creacion: datetime
    usuario_creacion_id: Optional[UUID]

    class Config:
        from_attributes = True


# ============================================================================
# PLAN DE INSPECCIÓN
# ============================================================================
class PlanInspeccionCreate(BaseModel):
    empresa_id: UUID
    codigo: str = Field(..., max_length=20)
    nombre: str = Field(..., max_length=100)
    descripcion: Optional[str] = Field(None, max_length=255)
    aplica_a: str = Field(..., max_length=20)  # 'producto', 'categoria', 'todos'
    producto_id: Optional[UUID] = None
    categoria_id: Optional[UUID] = None
    tipo_inspeccion: str = Field(..., max_length=30)  # 'recepcion', 'proceso', 'final', 'salida'
    tipo_muestreo: Optional[str] = Field("total", max_length=30)
    porcentaje_muestreo: Optional[Decimal] = Field(None, ge=0, le=100)
    tabla_muestreo: Optional[str] = Field(None, max_length=50)
    nivel_aceptacion_criticos: Optional[Decimal] = Field(0, ge=0)
    nivel_aceptacion_mayores: Optional[Decimal] = Field(2.5, ge=0)
    nivel_aceptacion_menores: Optional[Decimal] = Field(4.0, ge=0)
    es_activo: Optional[bool] = True
    fecha_vigencia_desde: Optional[date] = None
    fecha_vigencia_hasta: Optional[date] = None


class PlanInspeccionUpdate(BaseModel):
    codigo: Optional[str] = Field(None, max_length=20)
    nombre: Optional[str] = Field(None, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=255)
    aplica_a: Optional[str] = Field(None, max_length=20)
    producto_id: Optional[UUID] = None
    categoria_id: Optional[UUID] = None
    tipo_inspeccion: Optional[str] = Field(None, max_length=30)
    tipo_muestreo: Optional[str] = Field(None, max_length=30)
    porcentaje_muestreo: Optional[Decimal] = Field(None, ge=0, le=100)
    tabla_muestreo: Optional[str] = Field(None, max_length=50)
    nivel_aceptacion_criticos: Optional[Decimal] = Field(None, ge=0)
    nivel_aceptacion_mayores: Optional[Decimal] = Field(None, ge=0)
    nivel_aceptacion_menores: Optional[Decimal] = Field(None, ge=0)
    es_activo: Optional[bool] = None
    fecha_vigencia_desde: Optional[date] = None
    fecha_vigencia_hasta: Optional[date] = None


class PlanInspeccionRead(BaseModel):
    plan_inspeccion_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    codigo: str
    nombre: str
    descripcion: Optional[str]
    aplica_a: str
    producto_id: Optional[UUID]
    categoria_id: Optional[UUID]
    tipo_inspeccion: str
    tipo_muestreo: Optional[str]
    porcentaje_muestreo: Optional[Decimal]
    tabla_muestreo: Optional[str]
    nivel_aceptacion_criticos: Optional[Decimal]
    nivel_aceptacion_mayores: Optional[Decimal]
    nivel_aceptacion_menores: Optional[Decimal]
    es_activo: bool
    fecha_vigencia_desde: Optional[date]
    fecha_vigencia_hasta: Optional[date]
    fecha_creacion: datetime
    usuario_creacion_id: Optional[UUID]

    class Config:
        from_attributes = True


# ============================================================================
# PLAN DE INSPECCIÓN DETALLE
# ============================================================================
class PlanInspeccionDetalleCreate(BaseModel):
    plan_inspeccion_id: UUID
    parametro_calidad_id: UUID
    orden: Optional[int] = Field(0, ge=0)
    es_obligatorio: Optional[bool] = True
    criticidad: Optional[str] = Field("menor", max_length=20)  # 'critico', 'mayor', 'menor'
    valor_minimo_plan: Optional[Decimal] = None
    valor_maximo_plan: Optional[Decimal] = None
    valor_objetivo_plan: Optional[Decimal] = None
    instrucciones_especificas: Optional[str] = Field(None, max_length=500)


class PlanInspeccionDetalleUpdate(BaseModel):
    orden: Optional[int] = Field(None, ge=0)
    es_obligatorio: Optional[bool] = None
    criticidad: Optional[str] = Field(None, max_length=20)
    valor_minimo_plan: Optional[Decimal] = None
    valor_maximo_plan: Optional[Decimal] = None
    valor_objetivo_plan: Optional[Decimal] = None
    instrucciones_especificas: Optional[str] = Field(None, max_length=500)


class PlanInspeccionDetalleRead(BaseModel):
    plan_detalle_id: UUID
    cliente_id: UUID
    plan_inspeccion_id: UUID
    parametro_calidad_id: UUID
    orden: Optional[int]
    es_obligatorio: Optional[bool]
    criticidad: Optional[str]
    valor_minimo_plan: Optional[Decimal]
    valor_maximo_plan: Optional[Decimal]
    valor_objetivo_plan: Optional[Decimal]
    instrucciones_especificas: Optional[str]
    fecha_creacion: datetime

    class Config:
        from_attributes = True


# ============================================================================
# INSPECCIÓN
# ============================================================================
class InspeccionCreate(BaseModel):
    empresa_id: UUID
    numero_inspeccion: str = Field(..., max_length=20)
    fecha_inspeccion: Optional[datetime] = None
    plan_inspeccion_id: UUID
    producto_id: UUID
    lote: Optional[str] = Field(None, max_length=50)
    tipo_documento_origen: Optional[str] = Field(None, max_length=30)
    documento_origen_id: Optional[UUID] = None
    almacen_id: Optional[UUID] = None
    ubicacion_almacen: Optional[str] = Field(None, max_length=50)
    cantidad_total: Decimal = Field(..., ge=0)
    cantidad_inspeccionada: Decimal = Field(..., ge=0)
    unidad_medida_id: UUID
    cantidad_aprobada: Optional[Decimal] = Field(0, ge=0)
    cantidad_rechazada: Optional[Decimal] = Field(0, ge=0)
    cantidad_observada: Optional[Decimal] = Field(0, ge=0)
    defectos_criticos: Optional[int] = Field(0, ge=0)
    defectos_mayores: Optional[int] = Field(0, ge=0)
    defectos_menores: Optional[int] = Field(0, ge=0)
    resultado: Optional[str] = Field("pendiente", max_length=20)
    inspector_usuario_id: Optional[UUID] = None
    inspector_nombre: Optional[str] = Field(None, max_length=150)
    observaciones: Optional[str] = None
    acciones_correctivas: Optional[str] = None
    aprobado_por_usuario_id: Optional[UUID] = None
    fecha_aprobacion: Optional[datetime] = None


class InspeccionUpdate(BaseModel):
    numero_inspeccion: Optional[str] = Field(None, max_length=20)
    fecha_inspeccion: Optional[datetime] = None
    plan_inspeccion_id: Optional[UUID] = None
    producto_id: Optional[UUID] = None
    lote: Optional[str] = Field(None, max_length=50)
    tipo_documento_origen: Optional[str] = Field(None, max_length=30)
    documento_origen_id: Optional[UUID] = None
    almacen_id: Optional[UUID] = None
    ubicacion_almacen: Optional[str] = Field(None, max_length=50)
    cantidad_total: Optional[Decimal] = Field(None, ge=0)
    cantidad_inspeccionada: Optional[Decimal] = Field(None, ge=0)
    unidad_medida_id: Optional[UUID] = None
    cantidad_aprobada: Optional[Decimal] = Field(None, ge=0)
    cantidad_rechazada: Optional[Decimal] = Field(None, ge=0)
    cantidad_observada: Optional[Decimal] = Field(None, ge=0)
    defectos_criticos: Optional[int] = Field(None, ge=0)
    defectos_mayores: Optional[int] = Field(None, ge=0)
    defectos_menores: Optional[int] = Field(None, ge=0)
    resultado: Optional[str] = Field(None, max_length=20)
    inspector_usuario_id: Optional[UUID] = None
    inspector_nombre: Optional[str] = Field(None, max_length=150)
    observaciones: Optional[str] = None
    acciones_correctivas: Optional[str] = None
    aprobado_por_usuario_id: Optional[UUID] = None
    fecha_aprobacion: Optional[datetime] = None


class InspeccionRead(BaseModel):
    inspeccion_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    numero_inspeccion: str
    fecha_inspeccion: datetime
    plan_inspeccion_id: UUID
    producto_id: UUID
    lote: Optional[str]
    tipo_documento_origen: Optional[str]
    documento_origen_id: Optional[UUID]
    almacen_id: Optional[UUID]
    ubicacion_almacen: Optional[str]
    cantidad_total: Decimal
    cantidad_inspeccionada: Decimal
    unidad_medida_id: UUID
    cantidad_aprobada: Optional[Decimal]
    cantidad_rechazada: Optional[Decimal]
    cantidad_observada: Optional[Decimal]
    defectos_criticos: Optional[int]
    defectos_mayores: Optional[int]
    defectos_menores: Optional[int]
    resultado: Optional[str]
    inspector_usuario_id: Optional[UUID]
    inspector_nombre: Optional[str]
    observaciones: Optional[str]
    acciones_correctivas: Optional[str]
    aprobado_por_usuario_id: Optional[UUID]
    fecha_aprobacion: Optional[datetime]
    fecha_creacion: datetime
    usuario_creacion_id: Optional[UUID]

    class Config:
        from_attributes = True


# ============================================================================
# INSPECCIÓN DETALLE
# ============================================================================
class InspeccionDetalleCreate(BaseModel):
    inspeccion_id: UUID
    parametro_calidad_id: UUID
    valor_medido: Optional[Decimal] = None
    valor_cualitativo: Optional[str] = Field(None, max_length=50)
    resultado_pasa_no_pasa: Optional[bool] = None
    cumple_especificacion: Optional[bool] = True
    criticidad_defecto: Optional[str] = Field(None, max_length=20)
    observaciones: Optional[str] = Field(None, max_length=500)


class InspeccionDetalleUpdate(BaseModel):
    parametro_calidad_id: Optional[UUID] = None
    valor_medido: Optional[Decimal] = None
    valor_cualitativo: Optional[str] = Field(None, max_length=50)
    resultado_pasa_no_pasa: Optional[bool] = None
    cumple_especificacion: Optional[bool] = None
    criticidad_defecto: Optional[str] = Field(None, max_length=20)
    observaciones: Optional[str] = Field(None, max_length=500)


class InspeccionDetalleRead(BaseModel):
    inspeccion_detalle_id: UUID
    cliente_id: UUID
    inspeccion_id: UUID
    parametro_calidad_id: UUID
    valor_medido: Optional[Decimal]
    valor_cualitativo: Optional[str]
    resultado_pasa_no_pasa: Optional[bool]
    cumple_especificacion: Optional[bool]
    criticidad_defecto: Optional[str]
    observaciones: Optional[str]
    fecha_creacion: datetime

    class Config:
        from_attributes = True


# ============================================================================
# NO CONFORMIDAD
# ============================================================================
class NoConformidadCreate(BaseModel):
    empresa_id: UUID
    numero_nc: str = Field(..., max_length=20)
    fecha_deteccion: Optional[datetime] = None
    origen: str = Field(..., max_length=30)  # 'inspeccion', 'reclamo_cliente', 'auditoria', 'proceso'
    inspeccion_id: Optional[UUID] = None
    documento_referencia: Optional[str] = Field(None, max_length=50)
    producto_id: Optional[UUID] = None
    lote: Optional[str] = Field(None, max_length=50)
    cantidad_afectada: Optional[Decimal] = Field(None, ge=0)
    descripcion_nc: str
    tipo_nc: str = Field(..., max_length=30)  # 'critica', 'mayor', 'menor'
    area_responsable: Optional[str] = Field(None, max_length=100)
    responsable_usuario_id: Optional[UUID] = None
    analisis_causa_raiz: Optional[str] = None
    causa_raiz_identificada: Optional[str] = Field(None, max_length=500)
    accion_inmediata: Optional[str] = None
    accion_correctiva: Optional[str] = None
    accion_preventiva: Optional[str] = None
    responsable_accion_usuario_id: Optional[UUID] = None
    fecha_compromiso_cierre: Optional[date] = None
    estado: Optional[str] = Field("abierta", max_length=20)


class NoConformidadUpdate(BaseModel):
    numero_nc: Optional[str] = Field(None, max_length=20)
    fecha_deteccion: Optional[datetime] = None
    origen: Optional[str] = Field(None, max_length=30)
    inspeccion_id: Optional[UUID] = None
    documento_referencia: Optional[str] = Field(None, max_length=50)
    producto_id: Optional[UUID] = None
    lote: Optional[str] = Field(None, max_length=50)
    cantidad_afectada: Optional[Decimal] = Field(None, ge=0)
    descripcion_nc: Optional[str] = None
    tipo_nc: Optional[str] = Field(None, max_length=30)
    area_responsable: Optional[str] = Field(None, max_length=100)
    responsable_usuario_id: Optional[UUID] = None
    analisis_causa_raiz: Optional[str] = None
    causa_raiz_identificada: Optional[str] = Field(None, max_length=500)
    accion_inmediata: Optional[str] = None
    accion_correctiva: Optional[str] = None
    accion_preventiva: Optional[str] = None
    responsable_accion_usuario_id: Optional[UUID] = None
    fecha_compromiso_cierre: Optional[date] = None
    estado: Optional[str] = Field(None, max_length=20)
    fecha_cierre: Optional[datetime] = None
    cerrado_por_usuario_id: Optional[UUID] = None
    verificacion_eficacia: Optional[str] = None


class NoConformidadRead(BaseModel):
    no_conformidad_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    numero_nc: str
    fecha_deteccion: datetime
    origen: str
    inspeccion_id: Optional[UUID]
    documento_referencia: Optional[str]
    producto_id: Optional[UUID]
    lote: Optional[str]
    cantidad_afectada: Optional[Decimal]
    descripcion_nc: str
    tipo_nc: str
    area_responsable: Optional[str]
    responsable_usuario_id: Optional[UUID]
    analisis_causa_raiz: Optional[str]
    causa_raiz_identificada: Optional[str]
    accion_inmediata: Optional[str]
    accion_correctiva: Optional[str]
    accion_preventiva: Optional[str]
    responsable_accion_usuario_id: Optional[UUID]
    fecha_compromiso_cierre: Optional[date]
    estado: Optional[str]
    fecha_cierre: Optional[datetime]
    cerrado_por_usuario_id: Optional[UUID]
    verificacion_eficacia: Optional[str]
    fecha_creacion: datetime
    usuario_creacion_id: Optional[UUID]

    class Config:
        from_attributes = True
