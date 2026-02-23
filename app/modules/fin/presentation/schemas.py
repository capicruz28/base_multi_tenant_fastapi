# app/modules/fin/presentation/schemas.py
"""
Schemas Pydantic para el módulo FIN (Finanzas y Contabilidad).
Todos los Create/Update excluyen cliente_id; se asigna desde contexto en backend.
✅ Campos esenciales incluidos desde el inicio.
"""
from typing import Optional
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field


# ============================================================================
# PLAN DE CUENTAS
# ============================================================================
class PlanCuentaCreate(BaseModel):
    empresa_id: UUID
    codigo_cuenta: str = Field(..., max_length=20)
    nombre_cuenta: str = Field(..., max_length=200)
    descripcion: Optional[str] = Field(None, max_length=500)
    cuenta_padre_id: Optional[UUID] = None
    nivel: Optional[int] = Field(1, ge=1)
    ruta_jerarquica: Optional[str] = Field(None, max_length=500)
    tipo_cuenta: str = Field(..., max_length=20)  # 'activo', 'pasivo', 'patrimonio', 'ingreso', 'gasto'
    categoria: Optional[str] = Field(None, max_length=30)
    naturaleza: str = Field(..., max_length=10)  # 'deudora', 'acreedora'
    acepta_movimientos: Optional[bool] = True
    requiere_centro_costo: Optional[bool] = False
    requiere_documento_referencia: Optional[bool] = False
    requiere_tercero: Optional[bool] = False
    acepta_moneda_extranjera: Optional[bool] = True
    aparece_balance: Optional[bool] = True
    aparece_pyg: Optional[bool] = False
    codigo_sunat: Optional[str] = Field(None, max_length=10)
    es_activo: Optional[bool] = True


class PlanCuentaUpdate(BaseModel):
    codigo_cuenta: Optional[str] = Field(None, max_length=20)
    nombre_cuenta: Optional[str] = Field(None, max_length=200)
    descripcion: Optional[str] = Field(None, max_length=500)
    cuenta_padre_id: Optional[UUID] = None
    nivel: Optional[int] = Field(None, ge=1)
    ruta_jerarquica: Optional[str] = Field(None, max_length=500)
    tipo_cuenta: Optional[str] = Field(None, max_length=20)
    categoria: Optional[str] = Field(None, max_length=30)
    naturaleza: Optional[str] = Field(None, max_length=10)
    acepta_movimientos: Optional[bool] = None
    requiere_centro_costo: Optional[bool] = None
    requiere_documento_referencia: Optional[bool] = None
    requiere_tercero: Optional[bool] = None
    acepta_moneda_extranjera: Optional[bool] = None
    aparece_balance: Optional[bool] = None
    aparece_pyg: Optional[bool] = None
    codigo_sunat: Optional[str] = Field(None, max_length=10)
    es_activo: Optional[bool] = None


class PlanCuentaRead(BaseModel):
    cuenta_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    codigo_cuenta: str
    nombre_cuenta: str
    descripcion: Optional[str]
    cuenta_padre_id: Optional[UUID]
    nivel: Optional[int]
    ruta_jerarquica: Optional[str]
    tipo_cuenta: str
    categoria: Optional[str]
    naturaleza: str
    acepta_movimientos: Optional[bool]
    requiere_centro_costo: Optional[bool]
    requiere_documento_referencia: Optional[bool]
    requiere_tercero: Optional[bool]
    acepta_moneda_extranjera: Optional[bool]
    aparece_balance: Optional[bool]
    aparece_pyg: Optional[bool]
    codigo_sunat: Optional[str]
    es_activo: bool
    fecha_creacion: datetime
    usuario_creacion_id: Optional[UUID]

    class Config:
        from_attributes = True


# ============================================================================
# PERIODO CONTABLE
# ============================================================================
class PeriodoContableCreate(BaseModel):
    empresa_id: UUID
    año: int = Field(..., ge=2000, le=2100)
    mes: int = Field(..., ge=1, le=12)
    fecha_inicio: date
    fecha_fin: date
    estado: Optional[str] = Field("abierto", max_length=20)
    observaciones: Optional[str] = Field(None, max_length=500)


class PeriodoContableUpdate(BaseModel):
    año: Optional[int] = Field(None, ge=2000, le=2100)
    mes: Optional[int] = Field(None, ge=1, le=12)
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    estado: Optional[str] = Field(None, max_length=20)
    fecha_cierre: Optional[datetime] = None
    cerrado_por_usuario_id: Optional[UUID] = None
    observaciones: Optional[str] = Field(None, max_length=500)


class PeriodoContableRead(BaseModel):
    periodo_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    año: int
    mes: int
    fecha_inicio: date
    fecha_fin: date
    estado: str
    fecha_cierre: Optional[datetime]
    cerrado_por_usuario_id: Optional[UUID]
    observaciones: Optional[str]
    fecha_creacion: datetime

    class Config:
        from_attributes = True


# ============================================================================
# ASIENTO CONTABLE
# ============================================================================
class AsientoContableCreate(BaseModel):
    empresa_id: UUID
    numero_asiento: str = Field(..., max_length=20)
    fecha_asiento: date
    periodo_id: UUID
    tipo_asiento: str = Field(..., max_length=30)  # 'apertura', 'diario', 'ajuste', 'cierre', 'provision'
    modulo_origen: Optional[str] = Field(None, max_length=10)
    documento_origen_tipo: Optional[str] = Field(None, max_length=30)
    documento_origen_id: Optional[UUID] = None
    documento_origen_numero: Optional[str] = Field(None, max_length=30)
    glosa: str = Field(..., max_length=500)
    moneda: Optional[str] = Field("PEN", max_length=3)
    tipo_cambio: Optional[Decimal] = Field(1, ge=0)
    total_debe: Optional[Decimal] = Field(0, ge=0)
    total_haber: Optional[Decimal] = Field(0, ge=0)
    estado: Optional[str] = Field("borrador", max_length=20)
    requiere_aprobacion: Optional[bool] = False
    observaciones: Optional[str] = None


class AsientoContableUpdate(BaseModel):
    numero_asiento: Optional[str] = Field(None, max_length=20)
    fecha_asiento: Optional[date] = None
    periodo_id: Optional[UUID] = None
    tipo_asiento: Optional[str] = Field(None, max_length=30)
    modulo_origen: Optional[str] = Field(None, max_length=10)
    documento_origen_tipo: Optional[str] = Field(None, max_length=30)
    documento_origen_id: Optional[UUID] = None
    documento_origen_numero: Optional[str] = Field(None, max_length=30)
    glosa: Optional[str] = Field(None, max_length=500)
    moneda: Optional[str] = Field(None, max_length=3)
    tipo_cambio: Optional[Decimal] = Field(None, ge=0)
    total_debe: Optional[Decimal] = Field(None, ge=0)
    total_haber: Optional[Decimal] = Field(None, ge=0)
    estado: Optional[str] = Field(None, max_length=20)
    requiere_aprobacion: Optional[bool] = None
    aprobado_por_usuario_id: Optional[UUID] = None
    fecha_aprobacion: Optional[datetime] = None
    fecha_anulacion: Optional[datetime] = None
    motivo_anulacion: Optional[str] = Field(None, max_length=500)
    observaciones: Optional[str] = None


class AsientoContableRead(BaseModel):
    asiento_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    numero_asiento: str
    fecha_asiento: date
    periodo_id: UUID
    tipo_asiento: str
    modulo_origen: Optional[str]
    documento_origen_tipo: Optional[str]
    documento_origen_id: Optional[UUID]
    documento_origen_numero: Optional[str]
    glosa: str
    moneda: Optional[str]
    tipo_cambio: Optional[Decimal]
    total_debe: Optional[Decimal]
    total_haber: Optional[Decimal]
    estado: str
    requiere_aprobacion: Optional[bool]
    aprobado_por_usuario_id: Optional[UUID]
    fecha_aprobacion: Optional[datetime]
    fecha_anulacion: Optional[datetime]
    motivo_anulacion: Optional[str]
    observaciones: Optional[str]
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime]
    usuario_creacion_id: Optional[UUID]

    class Config:
        from_attributes = True


# ============================================================================
# ASIENTO DETALLE
# ============================================================================
class AsientoDetalleCreate(BaseModel):
    asiento_id: UUID
    item: int = Field(..., ge=1)
    cuenta_id: UUID
    debe: Optional[Decimal] = Field(0, ge=0)
    haber: Optional[Decimal] = Field(0, ge=0)
    debe_me: Optional[Decimal] = Field(0, ge=0)
    haber_me: Optional[Decimal] = Field(0, ge=0)
    glosa: Optional[str] = Field(None, max_length=500)
    centro_costo_id: Optional[UUID] = None
    documento_referencia: Optional[str] = Field(None, max_length=50)
    tercero_tipo: Optional[str] = Field(None, max_length=20)
    tercero_id: Optional[UUID] = None
    tercero_nombre: Optional[str] = Field(None, max_length=200)
    tercero_documento: Optional[str] = Field(None, max_length=20)
    fecha_vencimiento: Optional[date] = None


class AsientoDetalleUpdate(BaseModel):
    asiento_id: Optional[UUID] = None
    item: Optional[int] = Field(None, ge=1)
    cuenta_id: Optional[UUID] = None
    debe: Optional[Decimal] = Field(None, ge=0)
    haber: Optional[Decimal] = Field(None, ge=0)
    debe_me: Optional[Decimal] = Field(None, ge=0)
    haber_me: Optional[Decimal] = Field(None, ge=0)
    glosa: Optional[str] = Field(None, max_length=500)
    centro_costo_id: Optional[UUID] = None
    documento_referencia: Optional[str] = Field(None, max_length=50)
    tercero_tipo: Optional[str] = Field(None, max_length=20)
    tercero_id: Optional[UUID] = None
    tercero_nombre: Optional[str] = Field(None, max_length=200)
    tercero_documento: Optional[str] = Field(None, max_length=20)
    fecha_vencimiento: Optional[date] = None


class AsientoDetalleRead(BaseModel):
    asiento_detalle_id: UUID
    cliente_id: UUID
    asiento_id: UUID
    item: int
    cuenta_id: UUID
    debe: Optional[Decimal]
    haber: Optional[Decimal]
    debe_me: Optional[Decimal]
    haber_me: Optional[Decimal]
    glosa: Optional[str]
    centro_costo_id: Optional[UUID]
    documento_referencia: Optional[str]
    tercero_tipo: Optional[str]
    tercero_id: Optional[UUID]
    tercero_nombre: Optional[str]
    tercero_documento: Optional[str]
    fecha_vencimiento: Optional[date]
    fecha_creacion: datetime

    class Config:
        from_attributes = True
