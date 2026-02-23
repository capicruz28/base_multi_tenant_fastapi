# app/modules/prc/presentation/schemas.py
"""
Schemas Pydantic para el módulo PRC (Gestión de Precios y Promociones).
Todos los Create/Update excluyen cliente_id; se asigna desde contexto en backend.
✅ Campos esenciales incluidos desde el inicio.
"""
from typing import Optional, Any
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field


# ============================================================================
# LISTA DE PRECIO
# ============================================================================
class ListaPrecioCreate(BaseModel):
    empresa_id: UUID
    codigo_lista: str = Field(..., max_length=20)
    nombre: str = Field(..., max_length=100)
    descripcion: Optional[str] = Field(None, max_length=255)
    tipo_lista: Optional[str] = Field("general", max_length=30)  # 'general', 'mayorista', 'minorista', 'distribuidor', 'corporativo'
    moneda: Optional[str] = Field("PEN", max_length=3)
    fecha_vigencia_desde: date
    fecha_vigencia_hasta: Optional[date] = None
    incluye_igv: Optional[bool] = True
    permite_descuentos: Optional[bool] = True
    descuento_maximo_porcentaje: Optional[Decimal] = Field(10, ge=0, le=100)
    es_lista_defecto: Optional[bool] = False
    es_activo: Optional[bool] = True
    observaciones: Optional[str] = None


class ListaPrecioUpdate(BaseModel):
    codigo_lista: Optional[str] = Field(None, max_length=20)
    nombre: Optional[str] = Field(None, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=255)
    tipo_lista: Optional[str] = Field(None, max_length=30)
    moneda: Optional[str] = Field(None, max_length=3)
    fecha_vigencia_desde: Optional[date] = None
    fecha_vigencia_hasta: Optional[date] = None
    incluye_igv: Optional[bool] = None
    permite_descuentos: Optional[bool] = None
    descuento_maximo_porcentaje: Optional[Decimal] = Field(None, ge=0, le=100)
    es_lista_defecto: Optional[bool] = None
    es_activo: Optional[bool] = None
    observaciones: Optional[str] = None


class ListaPrecioRead(BaseModel):
    lista_precio_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    codigo_lista: str
    nombre: str
    descripcion: Optional[str]
    tipo_lista: Optional[str]
    moneda: Optional[str]
    fecha_vigencia_desde: date
    fecha_vigencia_hasta: Optional[date]
    incluye_igv: Optional[bool]
    permite_descuentos: Optional[bool]
    descuento_maximo_porcentaje: Optional[Decimal]
    es_lista_defecto: Optional[bool]
    es_activo: bool
    observaciones: Optional[str]
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime]
    usuario_creacion_id: Optional[UUID]

    class Config:
        from_attributes = True


# ============================================================================
# LISTA DE PRECIO DETALLE
# ============================================================================
class ListaPrecioDetalleCreate(BaseModel):
    lista_precio_id: UUID
    producto_id: UUID
    precio_unitario: Decimal = Field(..., ge=0)
    unidad_medida_id: UUID
    cantidad_minima: Optional[Decimal] = Field(1, ge=0)
    cantidad_maxima: Optional[Decimal] = Field(None, ge=0)
    descuento_maximo_porcentaje: Optional[Decimal] = Field(None, ge=0, le=100)
    fecha_vigencia_desde: Optional[date] = None
    fecha_vigencia_hasta: Optional[date] = None
    es_activo: Optional[bool] = True


class ListaPrecioDetalleUpdate(BaseModel):
    producto_id: Optional[UUID] = None
    precio_unitario: Optional[Decimal] = Field(None, ge=0)
    unidad_medida_id: Optional[UUID] = None
    cantidad_minima: Optional[Decimal] = Field(None, ge=0)
    cantidad_maxima: Optional[Decimal] = Field(None, ge=0)
    descuento_maximo_porcentaje: Optional[Decimal] = Field(None, ge=0, le=100)
    fecha_vigencia_desde: Optional[date] = None
    fecha_vigencia_hasta: Optional[date] = None
    es_activo: Optional[bool] = None


class ListaPrecioDetalleRead(BaseModel):
    lista_precio_detalle_id: UUID
    cliente_id: UUID
    lista_precio_id: UUID
    producto_id: UUID
    precio_unitario: Decimal
    unidad_medida_id: UUID
    cantidad_minima: Optional[Decimal]
    cantidad_maxima: Optional[Decimal]
    descuento_maximo_porcentaje: Optional[Decimal]
    fecha_vigencia_desde: Optional[date]
    fecha_vigencia_hasta: Optional[date]
    es_activo: bool
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime]

    class Config:
        from_attributes = True


# ============================================================================
# PROMOCIÓN
# ============================================================================
class PromocionCreate(BaseModel):
    empresa_id: UUID
    codigo_promocion: str = Field(..., max_length=20)
    nombre: str = Field(..., max_length=100)
    descripcion: Optional[str] = Field(None, max_length=500)
    tipo_promocion: str = Field(..., max_length=30)  # 'descuento_porcentaje', 'descuento_monto', '2x1', '3x2', 'producto_gratis'
    aplica_a: str = Field(..., max_length=20)  # 'producto', 'categoria', 'marca', 'toda_venta'
    producto_id: Optional[UUID] = None
    categoria_id: Optional[UUID] = None
    marca: Optional[str] = Field(None, max_length=100)
    descuento_porcentaje: Optional[Decimal] = Field(None, ge=0, le=100)
    descuento_monto: Optional[Decimal] = Field(None, ge=0)
    reglas_aplicacion: Optional[str] = None  # JSON string
    fecha_inicio: date
    fecha_fin: date
    cantidad_maxima_usos: Optional[int] = Field(None, ge=0)
    cantidad_usos_actuales: Optional[int] = Field(0, ge=0)
    monto_maximo_descuento: Optional[Decimal] = Field(None, ge=0)
    es_combinable: Optional[bool] = False
    aplica_canal_venta: Optional[str] = None  # JSON string
    es_activo: Optional[bool] = True
    requiere_codigo_cupon: Optional[bool] = False
    codigo_cupon: Optional[str] = Field(None, max_length=30)
    observaciones: Optional[str] = None


class PromocionUpdate(BaseModel):
    codigo_promocion: Optional[str] = Field(None, max_length=20)
    nombre: Optional[str] = Field(None, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=500)
    tipo_promocion: Optional[str] = Field(None, max_length=30)
    aplica_a: Optional[str] = Field(None, max_length=20)
    producto_id: Optional[UUID] = None
    categoria_id: Optional[UUID] = None
    marca: Optional[str] = Field(None, max_length=100)
    descuento_porcentaje: Optional[Decimal] = Field(None, ge=0, le=100)
    descuento_monto: Optional[Decimal] = Field(None, ge=0)
    reglas_aplicacion: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    cantidad_maxima_usos: Optional[int] = Field(None, ge=0)
    cantidad_usos_actuales: Optional[int] = Field(None, ge=0)
    monto_maximo_descuento: Optional[Decimal] = Field(None, ge=0)
    es_combinable: Optional[bool] = None
    aplica_canal_venta: Optional[str] = None
    es_activo: Optional[bool] = None
    requiere_codigo_cupon: Optional[bool] = None
    codigo_cupon: Optional[str] = Field(None, max_length=30)
    observaciones: Optional[str] = None


class PromocionRead(BaseModel):
    promocion_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    codigo_promocion: str
    nombre: str
    descripcion: Optional[str]
    tipo_promocion: str
    aplica_a: str
    producto_id: Optional[UUID]
    categoria_id: Optional[UUID]
    marca: Optional[str]
    descuento_porcentaje: Optional[Decimal]
    descuento_monto: Optional[Decimal]
    reglas_aplicacion: Optional[str]
    fecha_inicio: date
    fecha_fin: date
    cantidad_maxima_usos: Optional[int]
    cantidad_usos_actuales: Optional[int]
    monto_maximo_descuento: Optional[Decimal]
    es_combinable: Optional[bool]
    aplica_canal_venta: Optional[str]
    es_activo: bool
    requiere_codigo_cupon: Optional[bool]
    codigo_cupon: Optional[str]
    observaciones: Optional[str]
    fecha_creacion: datetime
    usuario_creacion_id: Optional[UUID]

    class Config:
        from_attributes = True
