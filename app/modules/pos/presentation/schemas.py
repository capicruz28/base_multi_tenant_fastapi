# app/modules/pos/presentation/schemas.py
"""
Schemas Pydantic para el módulo POS (Punto de Venta).
Create/Update no incluyen cliente_id; se asigna desde contexto en backend.
"""
from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


# ============================================================================
# PUNTO DE VENTA
# ============================================================================
class PuntoVentaCreate(BaseModel):
    empresa_id: UUID
    codigo_punto_venta: str = Field(..., max_length=20)
    nombre: str = Field(..., max_length=100)
    sucursal_id: UUID
    ubicacion_fisica: Optional[str] = Field(None, max_length=100)
    tipo_punto_venta: Optional[str] = Field("caja", max_length=30)
    serie_factura_id: Optional[UUID] = None
    serie_boleta_id: Optional[UUID] = None
    serie_nota_credito_id: Optional[UUID] = None
    almacen_id: Optional[UUID] = None
    lista_precio_id: Optional[UUID] = None
    acepta_efectivo: Optional[bool] = True
    acepta_tarjeta: Optional[bool] = True
    acepta_transferencia: Optional[bool] = True
    acepta_yape_plin: Optional[bool] = False
    codigo_terminal: Optional[str] = Field(None, max_length=50)
    ip_terminal: Optional[str] = Field(None, max_length=45)
    estado: Optional[str] = Field("cerrado", max_length=20)
    es_activo: Optional[bool] = True


class PuntoVentaUpdate(BaseModel):
    codigo_punto_venta: Optional[str] = Field(None, max_length=20)
    nombre: Optional[str] = Field(None, max_length=100)
    sucursal_id: Optional[UUID] = None
    ubicacion_fisica: Optional[str] = Field(None, max_length=100)
    tipo_punto_venta: Optional[str] = Field(None, max_length=30)
    serie_factura_id: Optional[UUID] = None
    serie_boleta_id: Optional[UUID] = None
    serie_nota_credito_id: Optional[UUID] = None
    almacen_id: Optional[UUID] = None
    lista_precio_id: Optional[UUID] = None
    acepta_efectivo: Optional[bool] = None
    acepta_tarjeta: Optional[bool] = None
    acepta_transferencia: Optional[bool] = None
    acepta_yape_plin: Optional[bool] = None
    codigo_terminal: Optional[str] = Field(None, max_length=50)
    ip_terminal: Optional[str] = Field(None, max_length=45)
    estado: Optional[str] = Field(None, max_length=20)
    es_activo: Optional[bool] = None


class PuntoVentaRead(BaseModel):
    punto_venta_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    codigo_punto_venta: str
    nombre: str
    sucursal_id: UUID
    ubicacion_fisica: Optional[str]
    tipo_punto_venta: Optional[str]
    serie_factura_id: Optional[UUID]
    serie_boleta_id: Optional[UUID]
    serie_nota_credito_id: Optional[UUID]
    almacen_id: Optional[UUID]
    lista_precio_id: Optional[UUID]
    acepta_efectivo: Optional[bool]
    acepta_tarjeta: Optional[bool]
    acepta_transferencia: Optional[bool]
    acepta_yape_plin: Optional[bool]
    codigo_terminal: Optional[str]
    ip_terminal: Optional[str]
    estado: Optional[str]
    es_activo: Optional[bool]
    fecha_creacion: datetime
    usuario_creacion_id: Optional[UUID]

    class Config:
        from_attributes = True


# ============================================================================
# TURNO DE CAJA
# ============================================================================
class TurnoCajaCreate(BaseModel):
    empresa_id: UUID
    punto_venta_id: UUID
    numero_turno: str = Field(..., max_length=20)
    cajero_usuario_id: UUID
    cajero_nombre: Optional[str] = Field(None, max_length=150)
    monto_apertura: Decimal = Field(..., ge=0)
    observaciones_apertura: Optional[str] = Field(None, max_length=500)
    estado: Optional[str] = Field("abierto", max_length=20)


class TurnoCajaUpdate(BaseModel):
    cajero_nombre: Optional[str] = Field(None, max_length=150)
    fecha_cierre: Optional[datetime] = None
    monto_cierre_esperado: Optional[Decimal] = Field(None, ge=0)
    monto_cierre_real: Optional[Decimal] = Field(None, ge=0)
    total_ventas: Optional[int] = Field(None, ge=0)
    total_ventas_efectivo: Optional[Decimal] = Field(None, ge=0)
    total_ventas_tarjeta: Optional[Decimal] = Field(None, ge=0)
    total_ventas_transferencia: Optional[Decimal] = Field(None, ge=0)
    total_ventas_otros: Optional[Decimal] = Field(None, ge=0)
    total_egresos: Optional[Decimal] = Field(None, ge=0)
    total_facturas: Optional[int] = Field(None, ge=0)
    total_boletas: Optional[int] = Field(None, ge=0)
    total_notas_credito: Optional[int] = Field(None, ge=0)
    estado: Optional[str] = Field(None, max_length=20)
    observaciones_cierre: Optional[str] = Field(None, max_length=500)
    cerrado_por_usuario_id: Optional[UUID] = None


class TurnoCajaRead(BaseModel):
    turno_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    punto_venta_id: UUID
    numero_turno: str
    cajero_usuario_id: UUID
    cajero_nombre: Optional[str]
    fecha_apertura: datetime
    monto_apertura: Decimal
    fecha_cierre: Optional[datetime]
    monto_cierre_esperado: Optional[Decimal]
    monto_cierre_real: Optional[Decimal]
    total_ventas: Optional[int]
    total_ventas_efectivo: Optional[Decimal]
    total_ventas_tarjeta: Optional[Decimal]
    total_ventas_transferencia: Optional[Decimal]
    total_ventas_otros: Optional[Decimal]
    total_egresos: Optional[Decimal]
    total_facturas: Optional[int]
    total_boletas: Optional[int]
    total_notas_credito: Optional[int]
    estado: Optional[str]
    observaciones_apertura: Optional[str]
    observaciones_cierre: Optional[str]
    fecha_creacion: datetime
    cerrado_por_usuario_id: Optional[UUID]

    class Config:
        from_attributes = True


# ============================================================================
# VENTA POS
# ============================================================================
class VentaCreate(BaseModel):
    empresa_id: UUID
    numero_venta: str = Field(..., max_length=20)
    punto_venta_id: UUID
    turno_caja_id: UUID
    vendedor_usuario_id: UUID
    vendedor_nombre: Optional[str] = Field(None, max_length=150)
    cliente_venta_id: Optional[UUID] = None
    cliente_nombre: Optional[str] = Field(None, max_length=200)
    cliente_documento_tipo: Optional[str] = Field(None, max_length=10)
    cliente_documento_numero: Optional[str] = Field(None, max_length=20)
    moneda: Optional[str] = Field("PEN", max_length=3)
    subtotal: Optional[Decimal] = Field(0, ge=0)
    descuento_global: Optional[Decimal] = Field(0, ge=0)
    igv: Optional[Decimal] = Field(0, ge=0)
    total: Optional[Decimal] = Field(0, ge=0)
    redondeo: Optional[Decimal] = Field(0, ge=0)
    forma_pago: str = Field(..., max_length=30)
    monto_efectivo: Optional[Decimal] = Field(0, ge=0)
    monto_tarjeta: Optional[Decimal] = Field(0, ge=0)
    monto_transferencia: Optional[Decimal] = Field(0, ge=0)
    monto_otros: Optional[Decimal] = Field(0, ge=0)
    monto_recibido: Optional[Decimal] = Field(None, ge=0)
    estado: Optional[str] = Field("completada", max_length=20)
    observaciones: Optional[str] = Field(None, max_length=500)


class VentaUpdate(BaseModel):
    vendedor_nombre: Optional[str] = Field(None, max_length=150)
    cliente_venta_id: Optional[UUID] = None
    cliente_nombre: Optional[str] = Field(None, max_length=200)
    cliente_documento_tipo: Optional[str] = Field(None, max_length=10)
    cliente_documento_numero: Optional[str] = Field(None, max_length=20)
    descuento_global: Optional[Decimal] = Field(None, ge=0)
    observaciones: Optional[str] = Field(None, max_length=500)
    fecha_anulacion: Optional[datetime] = None
    motivo_anulacion: Optional[str] = Field(None, max_length=500)
    estado: Optional[str] = Field(None, max_length=20)
    comprobante_id: Optional[UUID] = None
    tipo_comprobante: Optional[str] = Field(None, max_length=2)
    numero_comprobante: Optional[str] = Field(None, max_length=20)


class VentaRead(BaseModel):
    venta_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    numero_venta: str
    fecha_venta: datetime
    punto_venta_id: UUID
    turno_caja_id: UUID
    vendedor_usuario_id: UUID
    vendedor_nombre: Optional[str]
    cliente_venta_id: Optional[UUID]
    cliente_nombre: Optional[str]
    cliente_documento_tipo: Optional[str]
    cliente_documento_numero: Optional[str]
    moneda: Optional[str]
    subtotal: Optional[Decimal]
    descuento_global: Optional[Decimal]
    igv: Optional[Decimal]
    total: Optional[Decimal]
    redondeo: Optional[Decimal]
    forma_pago: str
    monto_efectivo: Optional[Decimal]
    monto_tarjeta: Optional[Decimal]
    monto_transferencia: Optional[Decimal]
    monto_otros: Optional[Decimal]
    monto_recibido: Optional[Decimal]
    comprobante_id: Optional[UUID]
    tipo_comprobante: Optional[str]
    numero_comprobante: Optional[str]
    estado: Optional[str]
    fecha_anulacion: Optional[datetime]
    motivo_anulacion: Optional[str]
    observaciones: Optional[str]
    fecha_creacion: datetime
    usuario_creacion_id: Optional[UUID]

    class Config:
        from_attributes = True


# ============================================================================
# VENTA DETALLE
# ============================================================================
class VentaDetalleCreate(BaseModel):
    venta_id: UUID
    item: int = Field(..., ge=1)
    producto_id: UUID
    descripcion: Optional[str] = Field(None, max_length=200)
    cantidad: Decimal = Field(..., gt=0)
    unidad_medida_id: UUID
    precio_unitario: Decimal = Field(..., ge=0)
    descuento_porcentaje: Optional[Decimal] = Field(0, ge=0, le=100)
    promocion_id: Optional[UUID] = None
    lote: Optional[str] = Field(None, max_length=50)


class VentaDetalleUpdate(BaseModel):
    descripcion: Optional[str] = Field(None, max_length=200)
    cantidad: Optional[Decimal] = Field(None, gt=0)
    unidad_medida_id: Optional[UUID] = None
    precio_unitario: Optional[Decimal] = Field(None, ge=0)
    descuento_porcentaje: Optional[Decimal] = Field(None, ge=0, le=100)
    promocion_id: Optional[UUID] = None
    lote: Optional[str] = Field(None, max_length=50)


class VentaDetalleRead(BaseModel):
    venta_detalle_id: UUID
    cliente_id: UUID
    venta_id: UUID
    item: int
    producto_id: UUID
    descripcion: Optional[str]
    cantidad: Decimal
    unidad_medida_id: UUID
    precio_unitario: Decimal
    descuento_porcentaje: Optional[Decimal]
    promocion_id: Optional[UUID]
    lote: Optional[str]
    fecha_creacion: datetime

    class Config:
        from_attributes = True
