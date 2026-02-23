# app/modules/sls/presentation/schemas.py
"""
Schemas Pydantic para el módulo SLS (Ventas).
Todos los Create/Update excluyen cliente_id; se asigna desde contexto en backend.
✅ Campos esenciales incluidos desde el inicio.
"""
from typing import Optional, Any
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field


# ============================================================================
# CLIENTE
# ============================================================================
class ClienteCreate(BaseModel):
    empresa_id: UUID
    codigo_cliente: str = Field(..., max_length=20)
    tipo_cliente: Optional[str] = Field("empresa", max_length=20)
    razon_social: str = Field(..., max_length=200)
    nombre_comercial: Optional[str] = Field(None, max_length=150)
    tipo_documento: Optional[str] = Field("RUC", max_length=10)
    numero_documento: str = Field(..., max_length=20)
    categoria_cliente: Optional[str] = Field(None, max_length=50)
    segmento: Optional[str] = Field(None, max_length=50)
    canal_venta: Optional[str] = Field(None, max_length=30)
    direccion: Optional[str] = Field(None, max_length=255)
    pais: Optional[str] = "Perú"
    departamento: Optional[str] = Field(None, max_length=50)
    provincia: Optional[str] = Field(None, max_length=50)
    distrito: Optional[str] = Field(None, max_length=50)
    ubigeo: Optional[str] = Field(None, max_length=6)
    contacto_nombre: Optional[str] = Field(None, max_length=150)
    contacto_cargo: Optional[str] = Field(None, max_length=100)
    telefono_principal: Optional[str] = Field(None, max_length=20)
    telefono_secundario: Optional[str] = Field(None, max_length=20)
    email_principal: Optional[str] = Field(None, max_length=100)
    email_facturacion: Optional[str] = Field(None, max_length=100)
    sitio_web: Optional[str] = Field(None, max_length=255)
    condicion_pago_defecto: Optional[str] = Field("contado", max_length=50)
    dias_credito_defecto: Optional[int] = 0
    moneda_preferida: Optional[str] = "PEN"
    lista_precio_id: Optional[UUID] = None
    limite_credito: Optional[Decimal] = None
    saldo_pendiente: Optional[Decimal] = Field(0, ge=0)
    saldo_vencido: Optional[Decimal] = Field(0, ge=0)
    vendedor_usuario_id: Optional[UUID] = None
    vendedor_nombre: Optional[str] = Field(None, max_length=150)
    banco: Optional[str] = Field(None, max_length=100)
    numero_cuenta: Optional[str] = Field(None, max_length=30)
    calificacion: Optional[Decimal] = Field(None, ge=0, le=5)
    nivel_riesgo: Optional[str] = Field("bajo", max_length=20)
    estado: Optional[str] = Field("activo", max_length=20)
    motivo_bloqueo: Optional[str] = Field(None, max_length=255)
    es_activo: Optional[bool] = True
    observaciones: Optional[str] = None


class ClienteUpdate(BaseModel):
    codigo_cliente: Optional[str] = Field(None, max_length=20)
    tipo_cliente: Optional[str] = Field(None, max_length=20)
    razon_social: Optional[str] = Field(None, max_length=200)
    nombre_comercial: Optional[str] = Field(None, max_length=150)
    tipo_documento: Optional[str] = Field(None, max_length=10)
    numero_documento: Optional[str] = Field(None, max_length=20)
    categoria_cliente: Optional[str] = Field(None, max_length=50)
    segmento: Optional[str] = Field(None, max_length=50)
    canal_venta: Optional[str] = Field(None, max_length=30)
    direccion: Optional[str] = Field(None, max_length=255)
    pais: Optional[str] = None
    departamento: Optional[str] = Field(None, max_length=50)
    provincia: Optional[str] = Field(None, max_length=50)
    distrito: Optional[str] = Field(None, max_length=50)
    ubigeo: Optional[str] = Field(None, max_length=6)
    contacto_nombre: Optional[str] = Field(None, max_length=150)
    contacto_cargo: Optional[str] = Field(None, max_length=100)
    telefono_principal: Optional[str] = Field(None, max_length=20)
    telefono_secundario: Optional[str] = Field(None, max_length=20)
    email_principal: Optional[str] = Field(None, max_length=100)
    email_facturacion: Optional[str] = Field(None, max_length=100)
    sitio_web: Optional[str] = Field(None, max_length=255)
    condicion_pago_defecto: Optional[str] = Field(None, max_length=50)
    dias_credito_defecto: Optional[int] = None
    moneda_preferida: Optional[str] = None
    lista_precio_id: Optional[UUID] = None
    limite_credito: Optional[Decimal] = None
    saldo_pendiente: Optional[Decimal] = None
    saldo_vencido: Optional[Decimal] = None
    vendedor_usuario_id: Optional[UUID] = None
    vendedor_nombre: Optional[str] = Field(None, max_length=150)
    banco: Optional[str] = Field(None, max_length=100)
    numero_cuenta: Optional[str] = Field(None, max_length=30)
    calificacion: Optional[Decimal] = None
    nivel_riesgo: Optional[str] = Field(None, max_length=20)
    estado: Optional[str] = Field(None, max_length=20)
    motivo_bloqueo: Optional[str] = Field(None, max_length=255)
    es_activo: Optional[bool] = None
    observaciones: Optional[str] = None


class ClienteRead(BaseModel):
    cliente_venta_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    codigo_cliente: str
    tipo_cliente: Optional[str]
    razon_social: str
    nombre_comercial: Optional[str]
    tipo_documento: Optional[str]
    numero_documento: str
    categoria_cliente: Optional[str]
    segmento: Optional[str]
    canal_venta: Optional[str]
    direccion: Optional[str]
    pais: Optional[str]
    departamento: Optional[str]
    provincia: Optional[str]
    distrito: Optional[str]
    ubigeo: Optional[str]
    contacto_nombre: Optional[str]
    contacto_cargo: Optional[str]
    telefono_principal: Optional[str]
    telefono_secundario: Optional[str]
    email_principal: Optional[str]
    email_facturacion: Optional[str]
    sitio_web: Optional[str]
    condicion_pago_defecto: Optional[str]
    dias_credito_defecto: Optional[int]
    moneda_preferida: Optional[str]
    lista_precio_id: Optional[UUID]
    limite_credito: Optional[Decimal]
    saldo_pendiente: Optional[Decimal]
    saldo_vencido: Optional[Decimal]
    vendedor_usuario_id: Optional[UUID]
    vendedor_nombre: Optional[str]
    banco: Optional[str]
    numero_cuenta: Optional[str]
    calificacion: Optional[Decimal]
    nivel_riesgo: Optional[str]
    estado: Optional[str]
    motivo_bloqueo: Optional[str]
    es_activo: bool
    observaciones: Optional[str]
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime]
    fecha_primera_compra: Optional[date]
    fecha_ultima_compra: Optional[date]
    usuario_creacion_id: Optional[UUID]

    class Config:
        from_attributes = True


# ============================================================================
# CONTACTO
# ============================================================================
class ClienteContactoCreate(BaseModel):
    cliente_venta_id: UUID
    nombre_completo: str = Field(..., max_length=150)
    cargo: Optional[str] = Field(None, max_length=100)
    area: Optional[str] = Field(None, max_length=100)
    telefono: Optional[str] = Field(None, max_length=20)
    telefono_movil: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    es_contacto_principal: Optional[bool] = False
    es_contacto_comercial: Optional[bool] = False
    es_contacto_cobranzas: Optional[bool] = False
    fecha_nacimiento: Optional[date] = None
    observaciones: Optional[str] = Field(None, max_length=500)
    es_activo: Optional[bool] = True


class ClienteContactoUpdate(BaseModel):
    nombre_completo: Optional[str] = Field(None, max_length=150)
    cargo: Optional[str] = Field(None, max_length=100)
    area: Optional[str] = Field(None, max_length=100)
    telefono: Optional[str] = Field(None, max_length=20)
    telefono_movil: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    es_contacto_principal: Optional[bool] = None
    es_contacto_comercial: Optional[bool] = None
    es_contacto_cobranzas: Optional[bool] = None
    fecha_nacimiento: Optional[date] = None
    observaciones: Optional[str] = Field(None, max_length=500)
    es_activo: Optional[bool] = None


class ClienteContactoRead(BaseModel):
    contacto_id: UUID
    cliente_id: UUID
    cliente_venta_id: UUID
    nombre_completo: str
    cargo: Optional[str]
    area: Optional[str]
    telefono: Optional[str]
    telefono_movil: Optional[str]
    email: Optional[str]
    es_contacto_principal: Optional[bool]
    es_contacto_comercial: Optional[bool]
    es_contacto_cobranzas: Optional[bool]
    fecha_nacimiento: Optional[date]
    observaciones: Optional[str]
    es_activo: bool
    fecha_creacion: datetime

    class Config:
        from_attributes = True


# ============================================================================
# DIRECCIÓN
# ============================================================================
class ClienteDireccionCreate(BaseModel):
    cliente_venta_id: UUID
    codigo_direccion: Optional[str] = Field(None, max_length=20)
    nombre_direccion: str = Field(..., max_length=100)
    direccion: str = Field(..., max_length=255)
    referencia: Optional[str] = Field(None, max_length=255)
    pais: Optional[str] = "Perú"
    departamento: Optional[str] = Field(None, max_length=50)
    provincia: Optional[str] = Field(None, max_length=50)
    distrito: Optional[str] = Field(None, max_length=50)
    ubigeo: Optional[str] = Field(None, max_length=6)
    codigo_postal: Optional[str] = Field(None, max_length=10)
    contacto_nombre: Optional[str] = Field(None, max_length=150)
    contacto_telefono: Optional[str] = Field(None, max_length=20)
    es_direccion_fiscal: Optional[bool] = False
    es_direccion_entrega_defecto: Optional[bool] = False
    es_activo: Optional[bool] = True


class ClienteDireccionUpdate(BaseModel):
    codigo_direccion: Optional[str] = Field(None, max_length=20)
    nombre_direccion: Optional[str] = Field(None, max_length=100)
    direccion: Optional[str] = Field(None, max_length=255)
    referencia: Optional[str] = Field(None, max_length=255)
    pais: Optional[str] = None
    departamento: Optional[str] = Field(None, max_length=50)
    provincia: Optional[str] = Field(None, max_length=50)
    distrito: Optional[str] = Field(None, max_length=50)
    ubigeo: Optional[str] = Field(None, max_length=6)
    codigo_postal: Optional[str] = Field(None, max_length=10)
    contacto_nombre: Optional[str] = Field(None, max_length=150)
    contacto_telefono: Optional[str] = Field(None, max_length=20)
    es_direccion_fiscal: Optional[bool] = None
    es_direccion_entrega_defecto: Optional[bool] = None
    es_activo: Optional[bool] = None


class ClienteDireccionRead(BaseModel):
    direccion_id: UUID
    cliente_id: UUID
    cliente_venta_id: UUID
    codigo_direccion: Optional[str]
    nombre_direccion: str
    direccion: str
    referencia: Optional[str]
    pais: Optional[str]
    departamento: Optional[str]
    provincia: Optional[str]
    distrito: Optional[str]
    ubigeo: Optional[str]
    codigo_postal: Optional[str]
    contacto_nombre: Optional[str]
    contacto_telefono: Optional[str]
    es_direccion_fiscal: Optional[bool]
    es_direccion_entrega_defecto: Optional[bool]
    es_activo: bool
    fecha_creacion: datetime

    class Config:
        from_attributes = True


# ============================================================================
# COTIZACIÓN
# ============================================================================
class CotizacionCreate(BaseModel):
    empresa_id: UUID
    numero_cotizacion: str = Field(..., max_length=20)
    fecha_cotizacion: Optional[date] = None
    fecha_vencimiento: date
    cliente_venta_id: UUID
    cliente_razon_social: Optional[str] = Field(None, max_length=200)
    cliente_ruc: Optional[str] = Field(None, max_length=20)
    contacto_nombre: Optional[str] = Field(None, max_length=150)
    vendedor_usuario_id: Optional[UUID] = None
    vendedor_nombre: Optional[str] = Field(None, max_length=150)
    oportunidad_id: Optional[UUID] = None
    condicion_pago: str = Field(..., max_length=50)
    dias_credito: Optional[int] = 0
    tiempo_entrega_dias: Optional[int] = None
    moneda: Optional[str] = "PEN"
    tipo_cambio: Optional[Decimal] = Field(1, ge=0)
    subtotal: Optional[Decimal] = Field(0, ge=0)
    descuento_global: Optional[Decimal] = Field(0, ge=0)
    igv: Optional[Decimal] = Field(0, ge=0)
    total: Optional[Decimal] = Field(0, ge=0)
    estado: Optional[str] = Field("borrador", max_length=20)
    fecha_envio: Optional[datetime] = None
    fecha_respuesta: Optional[datetime] = None
    motivo_rechazo: Optional[str] = Field(None, max_length=500)
    convertida_pedido: Optional[bool] = False
    pedido_venta_id: Optional[UUID] = None
    fecha_conversion: Optional[datetime] = None
    observaciones: Optional[str] = None
    terminos_condiciones: Optional[str] = None


class CotizacionUpdate(BaseModel):
    numero_cotizacion: Optional[str] = Field(None, max_length=20)
    fecha_cotizacion: Optional[date] = None
    fecha_vencimiento: Optional[date] = None
    cliente_venta_id: Optional[UUID] = None
    cliente_razon_social: Optional[str] = Field(None, max_length=200)
    cliente_ruc: Optional[str] = Field(None, max_length=20)
    contacto_nombre: Optional[str] = Field(None, max_length=150)
    vendedor_usuario_id: Optional[UUID] = None
    vendedor_nombre: Optional[str] = Field(None, max_length=150)
    oportunidad_id: Optional[UUID] = None
    condicion_pago: Optional[str] = Field(None, max_length=50)
    dias_credito: Optional[int] = None
    tiempo_entrega_dias: Optional[int] = None
    moneda: Optional[str] = None
    tipo_cambio: Optional[Decimal] = None
    subtotal: Optional[Decimal] = None
    descuento_global: Optional[Decimal] = None
    igv: Optional[Decimal] = None
    total: Optional[Decimal] = None
    estado: Optional[str] = Field(None, max_length=20)
    fecha_envio: Optional[datetime] = None
    fecha_respuesta: Optional[datetime] = None
    motivo_rechazo: Optional[str] = Field(None, max_length=500)
    convertida_pedido: Optional[bool] = None
    pedido_venta_id: Optional[UUID] = None
    fecha_conversion: Optional[datetime] = None
    observaciones: Optional[str] = None
    terminos_condiciones: Optional[str] = None


class CotizacionRead(BaseModel):
    cotizacion_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    numero_cotizacion: str
    fecha_cotizacion: date
    fecha_vencimiento: date
    cliente_venta_id: UUID
    cliente_razon_social: Optional[str]
    cliente_ruc: Optional[str]
    contacto_nombre: Optional[str]
    vendedor_usuario_id: Optional[UUID]
    vendedor_nombre: Optional[str]
    oportunidad_id: Optional[UUID]
    condicion_pago: str
    dias_credito: Optional[int]
    tiempo_entrega_dias: Optional[int]
    moneda: Optional[str]
    tipo_cambio: Optional[Decimal]
    subtotal: Optional[Decimal]
    descuento_global: Optional[Decimal]
    igv: Optional[Decimal]
    total: Optional[Decimal]
    estado: Optional[str]
    fecha_envio: Optional[datetime]
    fecha_respuesta: Optional[datetime]
    motivo_rechazo: Optional[str]
    convertida_pedido: Optional[bool]
    pedido_venta_id: Optional[UUID]
    fecha_conversion: Optional[datetime]
    observaciones: Optional[str]
    terminos_condiciones: Optional[str]
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime]
    usuario_creacion_id: Optional[UUID]

    class Config:
        from_attributes = True


# ============================================================================
# COTIZACIÓN DETALLE
# ============================================================================
class CotizacionDetalleCreate(BaseModel):
    cotizacion_id: UUID
    producto_id: UUID
    cantidad: Decimal = Field(..., ge=0)
    unidad_medida_id: UUID
    precio_unitario: Decimal = Field(..., ge=0)
    descuento_porcentaje: Optional[Decimal] = Field(0, ge=0, le=100)
    tiempo_entrega_dias: Optional[int] = None
    observaciones: Optional[str] = Field(None, max_length=500)


class CotizacionDetalleUpdate(BaseModel):
    producto_id: Optional[UUID] = None
    cantidad: Optional[Decimal] = Field(None, ge=0)
    unidad_medida_id: Optional[UUID] = None
    precio_unitario: Optional[Decimal] = Field(None, ge=0)
    descuento_porcentaje: Optional[Decimal] = Field(None, ge=0, le=100)
    tiempo_entrega_dias: Optional[int] = None
    observaciones: Optional[str] = Field(None, max_length=500)


class CotizacionDetalleRead(BaseModel):
    cotizacion_detalle_id: UUID
    cliente_id: UUID
    cotizacion_id: UUID
    producto_id: UUID
    cantidad: Decimal
    unidad_medida_id: UUID
    precio_unitario: Decimal
    descuento_porcentaje: Optional[Decimal]
    tiempo_entrega_dias: Optional[int]
    observaciones: Optional[str]
    fecha_creacion: datetime

    class Config:
        from_attributes = True


# ============================================================================
# PEDIDO
# ============================================================================
class PedidoCreate(BaseModel):
    empresa_id: UUID
    numero_pedido: str = Field(..., max_length=20)
    fecha_pedido: Optional[date] = None
    fecha_entrega_prometida: date
    cliente_venta_id: UUID
    cliente_razon_social: Optional[str] = Field(None, max_length=200)
    cliente_ruc: Optional[str] = Field(None, max_length=20)
    direccion_entrega_id: Optional[UUID] = None
    direccion_entrega_texto: Optional[str] = Field(None, max_length=255)
    cotizacion_id: Optional[UUID] = None
    orden_compra_cliente: Optional[str] = Field(None, max_length=30)
    vendedor_usuario_id: Optional[UUID] = None
    vendedor_nombre: Optional[str] = Field(None, max_length=150)
    condicion_pago: str = Field(..., max_length=50)
    dias_credito: Optional[int] = 0
    moneda: Optional[str] = "PEN"
    tipo_cambio: Optional[Decimal] = Field(1, ge=0)
    subtotal: Optional[Decimal] = Field(0, ge=0)
    descuento_global: Optional[Decimal] = Field(0, ge=0)
    igv: Optional[Decimal] = Field(0, ge=0)
    total: Optional[Decimal] = Field(0, ge=0)
    total_items: Optional[int] = Field(0, ge=0)
    items_despachados: Optional[int] = Field(0, ge=0)
    porcentaje_despacho: Optional[Decimal] = Field(0, ge=0, le=100)
    estado: Optional[str] = Field("borrador", max_length=20)
    requiere_aprobacion: Optional[bool] = False
    aprobado_por_usuario_id: Optional[UUID] = None
    fecha_aprobacion: Optional[datetime] = None
    prioridad: Optional[int] = Field(3, ge=1, le=4)
    centro_costo_id: Optional[UUID] = None
    observaciones: Optional[str] = None
    instrucciones_despacho: Optional[str] = None
    motivo_anulacion: Optional[str] = Field(None, max_length=500)


class PedidoUpdate(BaseModel):
    numero_pedido: Optional[str] = Field(None, max_length=20)
    fecha_pedido: Optional[date] = None
    fecha_entrega_prometida: Optional[date] = None
    cliente_venta_id: Optional[UUID] = None
    cliente_razon_social: Optional[str] = Field(None, max_length=200)
    cliente_ruc: Optional[str] = Field(None, max_length=20)
    direccion_entrega_id: Optional[UUID] = None
    direccion_entrega_texto: Optional[str] = Field(None, max_length=255)
    cotizacion_id: Optional[UUID] = None
    orden_compra_cliente: Optional[str] = Field(None, max_length=30)
    vendedor_usuario_id: Optional[UUID] = None
    vendedor_nombre: Optional[str] = Field(None, max_length=150)
    condicion_pago: Optional[str] = Field(None, max_length=50)
    dias_credito: Optional[int] = None
    moneda: Optional[str] = None
    tipo_cambio: Optional[Decimal] = None
    subtotal: Optional[Decimal] = None
    descuento_global: Optional[Decimal] = None
    igv: Optional[Decimal] = None
    total: Optional[Decimal] = None
    total_items: Optional[int] = None
    items_despachados: Optional[int] = None
    porcentaje_despacho: Optional[Decimal] = None
    estado: Optional[str] = Field(None, max_length=20)
    requiere_aprobacion: Optional[bool] = None
    aprobado_por_usuario_id: Optional[UUID] = None
    fecha_aprobacion: Optional[datetime] = None
    prioridad: Optional[int] = None
    centro_costo_id: Optional[UUID] = None
    observaciones: Optional[str] = None
    instrucciones_despacho: Optional[str] = None
    motivo_anulacion: Optional[str] = Field(None, max_length=500)


class PedidoRead(BaseModel):
    pedido_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    numero_pedido: str
    fecha_pedido: date
    fecha_entrega_prometida: date
    cliente_venta_id: UUID
    cliente_razon_social: Optional[str]
    cliente_ruc: Optional[str]
    direccion_entrega_id: Optional[UUID]
    direccion_entrega_texto: Optional[str]
    cotizacion_id: Optional[UUID]
    orden_compra_cliente: Optional[str]
    vendedor_usuario_id: Optional[UUID]
    vendedor_nombre: Optional[str]
    condicion_pago: str
    dias_credito: Optional[int]
    moneda: Optional[str]
    tipo_cambio: Optional[Decimal]
    subtotal: Optional[Decimal]
    descuento_global: Optional[Decimal]
    igv: Optional[Decimal]
    total: Optional[Decimal]
    total_items: Optional[int]
    items_despachados: Optional[int]
    porcentaje_despacho: Optional[Decimal]
    estado: Optional[str]
    requiere_aprobacion: Optional[bool]
    aprobado_por_usuario_id: Optional[UUID]
    fecha_aprobacion: Optional[datetime]
    prioridad: Optional[int]
    centro_costo_id: Optional[UUID]
    observaciones: Optional[str]
    instrucciones_despacho: Optional[str]
    motivo_anulacion: Optional[str]
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime]
    fecha_anulacion: Optional[datetime]
    usuario_creacion_id: Optional[UUID]

    class Config:
        from_attributes = True


# ============================================================================
# PEDIDO DETALLE
# ============================================================================
class PedidoDetalleCreate(BaseModel):
    pedido_id: UUID
    producto_id: UUID
    cantidad_pedida: Decimal = Field(..., ge=0)
    unidad_medida_id: UUID
    precio_unitario: Decimal = Field(..., ge=0)
    descuento_porcentaje: Optional[Decimal] = Field(0, ge=0, le=100)
    cantidad_despachada: Optional[Decimal] = Field(0, ge=0)
    cantidad_facturada: Optional[Decimal] = Field(0, ge=0)
    almacen_origen_id: Optional[UUID] = None
    observaciones: Optional[str] = Field(None, max_length=500)


class PedidoDetalleUpdate(BaseModel):
    producto_id: Optional[UUID] = None
    cantidad_pedida: Optional[Decimal] = Field(None, ge=0)
    unidad_medida_id: Optional[UUID] = None
    precio_unitario: Optional[Decimal] = Field(None, ge=0)
    descuento_porcentaje: Optional[Decimal] = Field(None, ge=0, le=100)
    cantidad_despachada: Optional[Decimal] = None
    cantidad_facturada: Optional[Decimal] = None
    almacen_origen_id: Optional[UUID] = None
    observaciones: Optional[str] = Field(None, max_length=500)


class PedidoDetalleRead(BaseModel):
    pedido_detalle_id: UUID
    cliente_id: UUID
    pedido_id: UUID
    producto_id: UUID
    cantidad_pedida: Decimal
    unidad_medida_id: UUID
    precio_unitario: Decimal
    descuento_porcentaje: Optional[Decimal]
    cantidad_despachada: Optional[Decimal]
    cantidad_facturada: Optional[Decimal]
    almacen_origen_id: Optional[UUID]
    observaciones: Optional[str]
    fecha_creacion: datetime

    class Config:
        from_attributes = True
