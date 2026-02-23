# app/modules/invbill/presentation/schemas.py
"""
Schemas Pydantic para el módulo INV_BILL (Facturación Electrónica).
Todos los Create/Update excluyen cliente_id; se asigna desde contexto en backend.
✅ Campos esenciales incluidos desde el inicio.
"""
from typing import Optional, Any
from uuid import UUID
from datetime import datetime, date, time
from decimal import Decimal
from pydantic import BaseModel, Field


# ============================================================================
# SERIE COMPROBANTE
# ============================================================================
class SerieComprobanteCreate(BaseModel):
    empresa_id: UUID
    tipo_comprobante: str = Field(..., max_length=2)  # '01'=Factura, '03'=Boleta, '07'=NC, '08'=ND
    serie: str = Field(..., max_length=4)  # 'F001', 'B001', etc
    numero_actual: Optional[int] = Field(0, ge=0)
    numero_inicial: Optional[int] = Field(1, ge=1)
    numero_final: Optional[int] = Field(None, ge=1)
    sucursal_id: Optional[UUID] = None
    punto_venta_id: Optional[UUID] = None
    es_electronica: Optional[bool] = True
    requiere_autorizacion_sunat: Optional[bool] = True
    es_activo: Optional[bool] = True
    fecha_activacion: Optional[date] = None
    fecha_baja: Optional[date] = None
    motivo_baja: Optional[str] = Field(None, max_length=255)


class SerieComprobanteUpdate(BaseModel):
    tipo_comprobante: Optional[str] = Field(None, max_length=2)
    serie: Optional[str] = Field(None, max_length=4)
    numero_actual: Optional[int] = Field(None, ge=0)
    numero_inicial: Optional[int] = Field(None, ge=1)
    numero_final: Optional[int] = Field(None, ge=1)
    sucursal_id: Optional[UUID] = None
    punto_venta_id: Optional[UUID] = None
    es_electronica: Optional[bool] = None
    requiere_autorizacion_sunat: Optional[bool] = None
    es_activo: Optional[bool] = None
    fecha_activacion: Optional[date] = None
    fecha_baja: Optional[date] = None
    motivo_baja: Optional[str] = Field(None, max_length=255)


class SerieComprobanteRead(BaseModel):
    serie_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    tipo_comprobante: str
    serie: str
    numero_actual: Optional[int]
    numero_inicial: Optional[int]
    numero_final: Optional[int]
    sucursal_id: Optional[UUID]
    punto_venta_id: Optional[UUID]
    es_electronica: Optional[bool]
    requiere_autorizacion_sunat: Optional[bool]
    es_activo: bool
    fecha_activacion: Optional[date]
    fecha_baja: Optional[date]
    motivo_baja: Optional[str]
    fecha_creacion: datetime
    usuario_creacion_id: Optional[UUID]

    class Config:
        from_attributes = True


# ============================================================================
# COMPROBANTE
# ============================================================================
class ComprobanteCreate(BaseModel):
    empresa_id: UUID
    tipo_comprobante: str = Field(..., max_length=2)  # '01', '03', '07', '08'
    serie: str = Field(..., max_length=4)
    numero: str = Field(..., max_length=10)
    fecha_emision: Optional[date] = None
    fecha_vencimiento: Optional[date] = None
    hora_emision: Optional[time] = None
    cliente_venta_id: Optional[UUID] = None
    cliente_tipo_documento: str = Field(..., max_length=2)  # '6'=RUC, '1'=DNI, etc
    cliente_numero_documento: str = Field(..., max_length=20)
    cliente_razon_social: str = Field(..., max_length=200)
    cliente_direccion: Optional[str] = Field(None, max_length=255)
    pedido_id: Optional[UUID] = None
    venta_id: Optional[UUID] = None
    guia_remision_id: Optional[UUID] = None
    comprobante_referencia_id: Optional[UUID] = None
    tipo_nota: Optional[str] = Field(None, max_length=2)
    motivo_nota: Optional[str] = Field(None, max_length=500)
    moneda: Optional[str] = Field("PEN", max_length=3)
    tipo_cambio: Optional[Decimal] = Field(1, ge=0)
    subtotal_gravado: Optional[Decimal] = Field(0, ge=0)
    subtotal_exonerado: Optional[Decimal] = Field(0, ge=0)
    subtotal_inafecto: Optional[Decimal] = Field(0, ge=0)
    subtotal_gratuito: Optional[Decimal] = Field(0, ge=0)
    descuento_global: Optional[Decimal] = Field(0, ge=0)
    igv: Optional[Decimal] = Field(0, ge=0)
    total: Optional[Decimal] = Field(0, ge=0)
    aplica_detraccion: Optional[bool] = False
    porcentaje_detraccion: Optional[Decimal] = Field(None, ge=0, le=100)
    monto_detraccion: Optional[Decimal] = Field(None, ge=0)
    aplica_retencion: Optional[bool] = False
    monto_retencion: Optional[Decimal] = Field(None, ge=0)
    aplica_percepcion: Optional[bool] = False
    monto_percepcion: Optional[Decimal] = Field(None, ge=0)
    condicion_pago: Optional[str] = Field(None, max_length=50)
    forma_pago: Optional[str] = Field("contado", max_length=30)
    codigo_hash: Optional[str] = Field(None, max_length=100)
    firma_digital: Optional[str] = None
    codigo_qr: Optional[str] = None
    estado_sunat: Optional[str] = Field("pendiente", max_length=20)
    codigo_respuesta_sunat: Optional[str] = Field(None, max_length=10)
    mensaje_respuesta_sunat: Optional[str] = Field(None, max_length=500)
    fecha_envio_sunat: Optional[datetime] = None
    fecha_respuesta_sunat: Optional[datetime] = None
    cdr_xml: Optional[str] = None
    cdr_fecha: Optional[datetime] = None
    xml_comprobante: Optional[str] = None
    pdf_url: Optional[str] = Field(None, max_length=500)
    estado: Optional[str] = Field("emitido", max_length=20)
    fecha_anulacion: Optional[datetime] = None
    motivo_anulacion: Optional[str] = Field(None, max_length=500)
    observaciones: Optional[str] = None
    vendedor_usuario_id: Optional[UUID] = None
    vendedor_nombre: Optional[str] = Field(None, max_length=150)


class ComprobanteUpdate(BaseModel):
    tipo_comprobante: Optional[str] = Field(None, max_length=2)
    serie: Optional[str] = Field(None, max_length=4)
    numero: Optional[str] = Field(None, max_length=10)
    fecha_emision: Optional[date] = None
    fecha_vencimiento: Optional[date] = None
    hora_emision: Optional[time] = None
    cliente_venta_id: Optional[UUID] = None
    cliente_tipo_documento: Optional[str] = Field(None, max_length=2)
    cliente_numero_documento: Optional[str] = Field(None, max_length=20)
    cliente_razon_social: Optional[str] = Field(None, max_length=200)
    cliente_direccion: Optional[str] = Field(None, max_length=255)
    pedido_id: Optional[UUID] = None
    venta_id: Optional[UUID] = None
    guia_remision_id: Optional[UUID] = None
    comprobante_referencia_id: Optional[UUID] = None
    tipo_nota: Optional[str] = Field(None, max_length=2)
    motivo_nota: Optional[str] = Field(None, max_length=500)
    moneda: Optional[str] = Field(None, max_length=3)
    tipo_cambio: Optional[Decimal] = None
    subtotal_gravado: Optional[Decimal] = None
    subtotal_exonerado: Optional[Decimal] = None
    subtotal_inafecto: Optional[Decimal] = None
    subtotal_gratuito: Optional[Decimal] = None
    descuento_global: Optional[Decimal] = None
    igv: Optional[Decimal] = None
    total: Optional[Decimal] = None
    aplica_detraccion: Optional[bool] = None
    porcentaje_detraccion: Optional[Decimal] = None
    monto_detraccion: Optional[Decimal] = None
    aplica_retencion: Optional[bool] = None
    monto_retencion: Optional[Decimal] = None
    aplica_percepcion: Optional[bool] = None
    monto_percepcion: Optional[Decimal] = None
    condicion_pago: Optional[str] = Field(None, max_length=50)
    forma_pago: Optional[str] = Field(None, max_length=30)
    codigo_hash: Optional[str] = Field(None, max_length=100)
    firma_digital: Optional[str] = None
    codigo_qr: Optional[str] = None
    estado_sunat: Optional[str] = Field(None, max_length=20)
    codigo_respuesta_sunat: Optional[str] = Field(None, max_length=10)
    mensaje_respuesta_sunat: Optional[str] = Field(None, max_length=500)
    fecha_envio_sunat: Optional[datetime] = None
    fecha_respuesta_sunat: Optional[datetime] = None
    cdr_xml: Optional[str] = None
    cdr_fecha: Optional[datetime] = None
    xml_comprobante: Optional[str] = None
    pdf_url: Optional[str] = Field(None, max_length=500)
    estado: Optional[str] = Field(None, max_length=20)
    fecha_anulacion: Optional[datetime] = None
    motivo_anulacion: Optional[str] = Field(None, max_length=500)
    observaciones: Optional[str] = None
    vendedor_usuario_id: Optional[UUID] = None
    vendedor_nombre: Optional[str] = Field(None, max_length=150)


class ComprobanteRead(BaseModel):
    comprobante_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    tipo_comprobante: str
    serie: str
    numero: str
    fecha_emision: date
    fecha_vencimiento: Optional[date]
    hora_emision: Optional[time]
    cliente_venta_id: Optional[UUID]
    cliente_tipo_documento: str
    cliente_numero_documento: str
    cliente_razon_social: str
    cliente_direccion: Optional[str]
    pedido_id: Optional[UUID]
    venta_id: Optional[UUID]
    guia_remision_id: Optional[UUID]
    comprobante_referencia_id: Optional[UUID]
    tipo_nota: Optional[str]
    motivo_nota: Optional[str]
    moneda: Optional[str]
    tipo_cambio: Optional[Decimal]
    subtotal_gravado: Optional[Decimal]
    subtotal_exonerado: Optional[Decimal]
    subtotal_inafecto: Optional[Decimal]
    subtotal_gratuito: Optional[Decimal]
    descuento_global: Optional[Decimal]
    igv: Optional[Decimal]
    total: Optional[Decimal]
    aplica_detraccion: Optional[bool]
    porcentaje_detraccion: Optional[Decimal]
    monto_detraccion: Optional[Decimal]
    aplica_retencion: Optional[bool]
    monto_retencion: Optional[Decimal]
    aplica_percepcion: Optional[bool]
    monto_percepcion: Optional[Decimal]
    condicion_pago: Optional[str]
    forma_pago: Optional[str]
    codigo_hash: Optional[str]
    firma_digital: Optional[str]
    codigo_qr: Optional[str]
    estado_sunat: Optional[str]
    codigo_respuesta_sunat: Optional[str]
    mensaje_respuesta_sunat: Optional[str]
    fecha_envio_sunat: Optional[datetime]
    fecha_respuesta_sunat: Optional[datetime]
    cdr_xml: Optional[str]
    cdr_fecha: Optional[datetime]
    xml_comprobante: Optional[str]
    pdf_url: Optional[str]
    estado: Optional[str]
    fecha_anulacion: Optional[datetime]
    motivo_anulacion: Optional[str]
    observaciones: Optional[str]
    vendedor_usuario_id: Optional[UUID]
    vendedor_nombre: Optional[str]
    fecha_creacion: datetime
    usuario_creacion_id: Optional[UUID]

    class Config:
        from_attributes = True


# ============================================================================
# COMPROBANTE DETALLE
# ============================================================================
class ComprobanteDetalleCreate(BaseModel):
    comprobante_id: UUID
    item: int = Field(..., ge=1)
    producto_id: Optional[UUID] = None
    codigo_producto: Optional[str] = Field(None, max_length=50)
    descripcion: str = Field(..., max_length=500)
    cantidad: Decimal = Field(..., ge=0)
    unidad_medida_codigo: str = Field(..., max_length=10)  # Código SUNAT (NIU, ZZ, etc)
    unidad_medida_id: Optional[UUID] = None
    precio_unitario: Decimal = Field(..., ge=0)
    descuento_unitario: Optional[Decimal] = Field(0, ge=0)
    tipo_afectacion_igv: str = Field(..., max_length=2)  # '10'=Gravado, '20'=Exonerado, etc
    porcentaje_igv: Optional[Decimal] = Field(18, ge=0, le=100)
    codigo_producto_sunat: Optional[str] = Field(None, max_length=10)
    lote: Optional[str] = Field(None, max_length=50)


class ComprobanteDetalleUpdate(BaseModel):
    item: Optional[int] = Field(None, ge=1)
    producto_id: Optional[UUID] = None
    codigo_producto: Optional[str] = Field(None, max_length=50)
    descripcion: Optional[str] = Field(None, max_length=500)
    cantidad: Optional[Decimal] = Field(None, ge=0)
    unidad_medida_codigo: Optional[str] = Field(None, max_length=10)
    unidad_medida_id: Optional[UUID] = None
    precio_unitario: Optional[Decimal] = Field(None, ge=0)
    descuento_unitario: Optional[Decimal] = Field(None, ge=0)
    tipo_afectacion_igv: Optional[str] = Field(None, max_length=2)
    porcentaje_igv: Optional[Decimal] = Field(None, ge=0, le=100)
    codigo_producto_sunat: Optional[str] = Field(None, max_length=10)
    lote: Optional[str] = Field(None, max_length=50)


class ComprobanteDetalleRead(BaseModel):
    comprobante_detalle_id: UUID
    cliente_id: UUID
    comprobante_id: UUID
    item: int
    producto_id: Optional[UUID]
    codigo_producto: Optional[str]
    descripcion: str
    cantidad: Decimal
    unidad_medida_codigo: str
    unidad_medida_id: Optional[UUID]
    precio_unitario: Decimal
    descuento_unitario: Optional[Decimal]
    tipo_afectacion_igv: str
    porcentaje_igv: Optional[Decimal]
    codigo_producto_sunat: Optional[str]
    lote: Optional[str]
    fecha_creacion: datetime

    class Config:
        from_attributes = True
