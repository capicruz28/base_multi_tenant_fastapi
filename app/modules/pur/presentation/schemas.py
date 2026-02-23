# app/modules/pur/presentation/schemas.py
"""
Schemas Pydantic para el módulo PUR (Compras).
Todos los Create/Update excluyen cliente_id; se asigna desde contexto en backend.
✅ Campos esenciales incluidos desde el inicio.
"""
from typing import Optional, Any
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field


# ============================================================================
# PROVEEDOR
# ============================================================================
class ProveedorCreate(BaseModel):
    empresa_id: UUID
    codigo_proveedor: str = Field(..., max_length=20)
    razon_social: str = Field(..., max_length=200)
    nombre_comercial: Optional[str] = Field(None, max_length=150)
    tipo_documento: Optional[str] = Field("RUC", max_length=10)
    numero_documento: str = Field(..., max_length=20)
    tipo_proveedor: Optional[str] = Field("bienes", max_length=30)
    categoria_proveedor: Optional[str] = Field(None, max_length=50)
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
    email_cotizaciones: Optional[str] = Field(None, max_length=100)
    sitio_web: Optional[str] = Field(None, max_length=255)
    condicion_pago_defecto: Optional[str] = Field(None, max_length=50)
    dias_credito_defecto: Optional[int] = 0
    moneda_preferida: Optional[str] = "PEN"
    banco: Optional[str] = Field(None, max_length=100)
    numero_cuenta: Optional[str] = Field(None, max_length=30)
    tipo_cuenta: Optional[str] = Field(None, max_length=20)
    cci: Optional[str] = Field(None, max_length=20)
    calificacion: Optional[Decimal] = Field(None, ge=0, le=5)
    nivel_confianza: Optional[str] = Field("medio", max_length=20)
    es_proveedor_homologado: Optional[bool] = False
    fecha_homologacion: Optional[date] = None
    limite_credito: Optional[Decimal] = None
    saldo_pendiente: Optional[Decimal] = Field(0, ge=0)
    estado: Optional[str] = Field("activo", max_length=20)
    motivo_bloqueo: Optional[str] = Field(None, max_length=255)
    es_activo: Optional[bool] = True
    observaciones: Optional[str] = None


class ProveedorUpdate(BaseModel):
    codigo_proveedor: Optional[str] = Field(None, max_length=20)
    razon_social: Optional[str] = Field(None, max_length=200)
    nombre_comercial: Optional[str] = Field(None, max_length=150)
    tipo_documento: Optional[str] = Field(None, max_length=10)
    numero_documento: Optional[str] = Field(None, max_length=20)
    tipo_proveedor: Optional[str] = Field(None, max_length=30)
    categoria_proveedor: Optional[str] = Field(None, max_length=50)
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
    email_cotizaciones: Optional[str] = Field(None, max_length=100)
    sitio_web: Optional[str] = Field(None, max_length=255)
    condicion_pago_defecto: Optional[str] = Field(None, max_length=50)
    dias_credito_defecto: Optional[int] = None
    moneda_preferida: Optional[str] = None
    banco: Optional[str] = Field(None, max_length=100)
    numero_cuenta: Optional[str] = Field(None, max_length=30)
    tipo_cuenta: Optional[str] = Field(None, max_length=20)
    cci: Optional[str] = Field(None, max_length=20)
    calificacion: Optional[Decimal] = None
    nivel_confianza: Optional[str] = Field(None, max_length=20)
    es_proveedor_homologado: Optional[bool] = None
    fecha_homologacion: Optional[date] = None
    limite_credito: Optional[Decimal] = None
    saldo_pendiente: Optional[Decimal] = None
    estado: Optional[str] = Field(None, max_length=20)
    motivo_bloqueo: Optional[str] = Field(None, max_length=255)
    es_activo: Optional[bool] = None
    observaciones: Optional[str] = None


class ProveedorRead(BaseModel):
    proveedor_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    codigo_proveedor: str
    razon_social: str
    nombre_comercial: Optional[str] = None
    tipo_documento: Optional[str] = None
    numero_documento: str
    tipo_proveedor: Optional[str] = None
    categoria_proveedor: Optional[str] = None
    direccion: Optional[str] = None
    pais: Optional[str] = None
    departamento: Optional[str] = None
    provincia: Optional[str] = None
    distrito: Optional[str] = None
    ubigeo: Optional[str] = None
    contacto_nombre: Optional[str] = None
    contacto_cargo: Optional[str] = None
    telefono_principal: Optional[str] = None
    telefono_secundario: Optional[str] = None
    email_principal: Optional[str] = None
    email_cotizaciones: Optional[str] = None
    sitio_web: Optional[str] = None
    condicion_pago_defecto: Optional[str] = None
    dias_credito_defecto: Optional[int] = None
    moneda_preferida: Optional[str] = None
    banco: Optional[str] = None
    numero_cuenta: Optional[str] = None
    tipo_cuenta: Optional[str] = None
    cci: Optional[str] = None
    calificacion: Optional[Decimal] = None
    nivel_confianza: Optional[str] = None
    es_proveedor_homologado: Optional[bool] = None
    fecha_homologacion: Optional[date] = None
    limite_credito: Optional[Decimal] = None
    saldo_pendiente: Optional[Decimal] = None
    estado: Optional[str] = None
    motivo_bloqueo: Optional[str] = None
    es_activo: bool
    observaciones: Optional[str] = None
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None
    usuario_creacion_id: Optional[UUID] = None
    usuario_actualizacion_id: Optional[UUID] = None

    class Config:
        from_attributes = True


# ============================================================================
# CONTACTO DE PROVEEDOR
# ============================================================================
class ContactoProveedorCreate(BaseModel):
    proveedor_id: UUID
    nombre_completo: str = Field(..., max_length=150)
    cargo: Optional[str] = Field(None, max_length=100)
    area: Optional[str] = Field(None, max_length=100)
    telefono: Optional[str] = Field(None, max_length=20)
    telefono_movil: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    es_contacto_principal: Optional[bool] = False
    es_contacto_cotizaciones: Optional[bool] = False
    es_contacto_cobranzas: Optional[bool] = False
    es_activo: Optional[bool] = True


class ContactoProveedorUpdate(BaseModel):
    nombre_completo: Optional[str] = Field(None, max_length=150)
    cargo: Optional[str] = Field(None, max_length=100)
    area: Optional[str] = Field(None, max_length=100)
    telefono: Optional[str] = Field(None, max_length=20)
    telefono_movil: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    es_contacto_principal: Optional[bool] = None
    es_contacto_cotizaciones: Optional[bool] = None
    es_contacto_cobranzas: Optional[bool] = None
    es_activo: Optional[bool] = None


class ContactoProveedorRead(BaseModel):
    contacto_id: UUID
    cliente_id: UUID
    proveedor_id: UUID
    nombre_completo: str
    cargo: Optional[str] = None
    area: Optional[str] = None
    telefono: Optional[str] = None
    telefono_movil: Optional[str] = None
    email: Optional[str] = None
    es_contacto_principal: Optional[bool] = None
    es_contacto_cotizaciones: Optional[bool] = None
    es_contacto_cobranzas: Optional[bool] = None
    es_activo: bool
    fecha_creacion: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# PRODUCTO POR PROVEEDOR
# ============================================================================
class ProductoProveedorCreate(BaseModel):
    proveedor_id: UUID
    producto_id: UUID
    codigo_proveedor: Optional[str] = Field(None, max_length=50)
    descripcion_proveedor: Optional[str] = Field(None, max_length=200)
    precio_unitario: Decimal = Field(..., ge=0)
    moneda: Optional[str] = "PEN"
    unidad_medida_id: UUID
    cantidad_minima: Optional[Decimal] = None
    multiplo_compra: Optional[Decimal] = None
    tiempo_entrega_dias: Optional[int] = None
    fecha_vigencia_desde: Optional[date] = None
    fecha_vigencia_hasta: Optional[date] = None
    es_proveedor_preferido: Optional[bool] = False
    prioridad: Optional[int] = Field(3, ge=1, le=10)
    es_activo: Optional[bool] = True


class ProductoProveedorUpdate(BaseModel):
    codigo_proveedor: Optional[str] = Field(None, max_length=50)
    descripcion_proveedor: Optional[str] = Field(None, max_length=200)
    precio_unitario: Optional[Decimal] = Field(None, ge=0)
    moneda: Optional[str] = None
    unidad_medida_id: Optional[UUID] = None
    cantidad_minima: Optional[Decimal] = None
    multiplo_compra: Optional[Decimal] = None
    tiempo_entrega_dias: Optional[int] = None
    fecha_vigencia_desde: Optional[date] = None
    fecha_vigencia_hasta: Optional[date] = None
    es_proveedor_preferido: Optional[bool] = None
    prioridad: Optional[int] = Field(None, ge=1, le=10)
    es_activo: Optional[bool] = None


class ProductoProveedorRead(BaseModel):
    producto_proveedor_id: UUID
    cliente_id: UUID
    proveedor_id: UUID
    producto_id: UUID
    codigo_proveedor: Optional[str] = None
    descripcion_proveedor: Optional[str] = None
    precio_unitario: Decimal
    moneda: Optional[str] = None
    unidad_medida_id: UUID
    cantidad_minima: Optional[Decimal] = None
    multiplo_compra: Optional[Decimal] = None
    tiempo_entrega_dias: Optional[int] = None
    fecha_vigencia_desde: Optional[date] = None
    fecha_vigencia_hasta: Optional[date] = None
    es_proveedor_preferido: Optional[bool] = None
    prioridad: Optional[int] = None
    es_activo: bool
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# SOLICITUD DE COMPRA
# ============================================================================
class SolicitudCompraCreate(BaseModel):
    empresa_id: UUID
    numero_solicitud: str = Field(..., max_length=20)
    fecha_solicitud: Optional[date] = None
    fecha_requerida: date
    departamento_solicitante_id: Optional[UUID] = None
    usuario_solicitante_id: UUID
    solicitante_nombre: Optional[str] = Field(None, max_length=150)
    almacen_destino_id: Optional[UUID] = None
    centro_costo_id: Optional[UUID] = None
    tipo_solicitud: Optional[str] = Field("normal", max_length=30)
    motivo_solicitud: Optional[str] = Field(None, max_length=30)
    total_items: Optional[int] = 0
    total_estimado: Optional[Decimal] = Field(0, ge=0)
    moneda: Optional[str] = "PEN"
    estado: Optional[str] = Field("borrador", max_length=20)
    requiere_aprobacion: Optional[bool] = True
    observaciones: Optional[str] = None


class SolicitudCompraUpdate(BaseModel):
    numero_solicitud: Optional[str] = Field(None, max_length=20)
    fecha_solicitud: Optional[date] = None
    fecha_requerida: Optional[date] = None
    departamento_solicitante_id: Optional[UUID] = None
    usuario_solicitante_id: Optional[UUID] = None
    solicitante_nombre: Optional[str] = Field(None, max_length=150)
    almacen_destino_id: Optional[UUID] = None
    centro_costo_id: Optional[UUID] = None
    tipo_solicitud: Optional[str] = Field(None, max_length=30)
    motivo_solicitud: Optional[str] = Field(None, max_length=30)
    total_items: Optional[int] = None
    total_estimado: Optional[Decimal] = None
    moneda: Optional[str] = None
    estado: Optional[str] = Field(None, max_length=20)
    requiere_aprobacion: Optional[bool] = None
    aprobado_por_usuario_id: Optional[UUID] = None
    fecha_aprobacion: Optional[datetime] = None
    orden_compra_generada: Optional[bool] = None
    observaciones: Optional[str] = None
    motivo_rechazo: Optional[str] = Field(None, max_length=500)


class SolicitudCompraRead(BaseModel):
    solicitud_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    numero_solicitud: str
    fecha_solicitud: date
    fecha_requerida: date
    departamento_solicitante_id: Optional[UUID] = None
    usuario_solicitante_id: UUID
    solicitante_nombre: Optional[str] = None
    almacen_destino_id: Optional[UUID] = None
    centro_costo_id: Optional[UUID] = None
    tipo_solicitud: Optional[str] = None
    motivo_solicitud: Optional[str] = None
    total_items: Optional[int] = None
    total_estimado: Optional[Decimal] = None
    moneda: Optional[str] = None
    estado: str
    requiere_aprobacion: Optional[bool] = None
    aprobado_por_usuario_id: Optional[UUID] = None
    fecha_aprobacion: Optional[datetime] = None
    orden_compra_generada: Optional[bool] = None
    observaciones: Optional[str] = None
    motivo_rechazo: Optional[str] = None
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None
    usuario_creacion_id: Optional[UUID] = None

    class Config:
        from_attributes = True


# ============================================================================
# COTIZACIÓN
# ============================================================================
class CotizacionCreate(BaseModel):
    empresa_id: UUID
    numero_cotizacion: str = Field(..., max_length=20)
    fecha_cotizacion: Optional[date] = None
    fecha_vencimiento: Optional[date] = None
    proveedor_id: UUID
    solicitud_compra_id: Optional[UUID] = None
    condicion_pago: Optional[str] = Field(None, max_length=50)
    dias_credito: Optional[int] = None
    tiempo_entrega_dias: Optional[int] = None
    lugar_entrega: Optional[str] = Field(None, max_length=255)
    moneda: Optional[str] = "PEN"
    subtotal: Optional[Decimal] = Field(0, ge=0)
    descuento: Optional[Decimal] = Field(0, ge=0)
    igv: Optional[Decimal] = Field(0, ge=0)
    total: Optional[Decimal] = Field(0, ge=0)
    estado: Optional[str] = Field("pendiente", max_length=20)
    es_ganadora: Optional[bool] = False
    observaciones: Optional[str] = None


class CotizacionUpdate(BaseModel):
    numero_cotizacion: Optional[str] = Field(None, max_length=20)
    fecha_cotizacion: Optional[date] = None
    fecha_vencimiento: Optional[date] = None
    proveedor_id: Optional[UUID] = None
    solicitud_compra_id: Optional[UUID] = None
    condicion_pago: Optional[str] = Field(None, max_length=50)
    dias_credito: Optional[int] = None
    tiempo_entrega_dias: Optional[int] = None
    lugar_entrega: Optional[str] = Field(None, max_length=255)
    moneda: Optional[str] = None
    subtotal: Optional[Decimal] = None
    descuento: Optional[Decimal] = None
    igv: Optional[Decimal] = None
    total: Optional[Decimal] = None
    estado: Optional[str] = Field(None, max_length=20)
    es_ganadora: Optional[bool] = None
    observaciones: Optional[str] = None
    motivo_rechazo: Optional[str] = Field(None, max_length=500)


class CotizacionRead(BaseModel):
    cotizacion_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    numero_cotizacion: str
    fecha_cotizacion: date
    fecha_vencimiento: Optional[date] = None
    proveedor_id: UUID
    solicitud_compra_id: Optional[UUID] = None
    condicion_pago: Optional[str] = None
    dias_credito: Optional[int] = None
    tiempo_entrega_dias: Optional[int] = None
    lugar_entrega: Optional[str] = None
    moneda: Optional[str] = None
    subtotal: Optional[Decimal] = None
    descuento: Optional[Decimal] = None
    igv: Optional[Decimal] = None
    total: Optional[Decimal] = None
    estado: str
    es_ganadora: Optional[bool] = None
    observaciones: Optional[str] = None
    motivo_rechazo: Optional[str] = None
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None
    usuario_creacion_id: Optional[UUID] = None

    class Config:
        from_attributes = True


# ============================================================================
# ORDEN DE COMPRA
# ============================================================================
class OrdenCompraCreate(BaseModel):
    empresa_id: UUID
    numero_oc: str = Field(..., max_length=20)
    fecha_emision: Optional[date] = None
    fecha_requerida: date
    proveedor_id: UUID
    proveedor_razon_social: Optional[str] = Field(None, max_length=200)
    proveedor_ruc: Optional[str] = Field(None, max_length=20)
    almacen_destino_id: Optional[UUID] = None
    direccion_entrega: Optional[str] = Field(None, max_length=255)
    solicitud_compra_id: Optional[UUID] = None
    cotizacion_id: Optional[UUID] = None
    condicion_pago: str = Field(..., max_length=50)
    dias_credito: Optional[int] = Field(0, ge=0)
    moneda: Optional[str] = "PEN"
    tipo_cambio: Optional[Decimal] = Field(1, ge=0)
    subtotal: Optional[Decimal] = Field(0, ge=0)
    descuento_global: Optional[Decimal] = Field(0, ge=0)
    igv: Optional[Decimal] = Field(0, ge=0)
    total: Optional[Decimal] = Field(0, ge=0)
    total_items: Optional[int] = 0
    estado: Optional[str] = Field("borrador", max_length=20)
    requiere_aprobacion: Optional[bool] = True
    centro_costo_id: Optional[UUID] = None
    observaciones: Optional[str] = None
    terminos_condiciones: Optional[str] = None


class OrdenCompraUpdate(BaseModel):
    numero_oc: Optional[str] = Field(None, max_length=20)
    fecha_emision: Optional[date] = None
    fecha_requerida: Optional[date] = None
    proveedor_id: Optional[UUID] = None
    proveedor_razon_social: Optional[str] = Field(None, max_length=200)
    proveedor_ruc: Optional[str] = Field(None, max_length=20)
    almacen_destino_id: Optional[UUID] = None
    direccion_entrega: Optional[str] = Field(None, max_length=255)
    solicitud_compra_id: Optional[UUID] = None
    cotizacion_id: Optional[UUID] = None
    condicion_pago: Optional[str] = Field(None, max_length=50)
    dias_credito: Optional[int] = None
    moneda: Optional[str] = None
    tipo_cambio: Optional[Decimal] = None
    subtotal: Optional[Decimal] = None
    descuento_global: Optional[Decimal] = None
    igv: Optional[Decimal] = None
    total: Optional[Decimal] = None
    total_items: Optional[int] = None
    items_recepcionados: Optional[int] = None
    porcentaje_recepcion: Optional[Decimal] = None
    estado: Optional[str] = Field(None, max_length=20)
    requiere_aprobacion: Optional[bool] = None
    aprobado_por_usuario_id: Optional[UUID] = None
    fecha_aprobacion: Optional[datetime] = None
    centro_costo_id: Optional[UUID] = None
    observaciones: Optional[str] = None
    terminos_condiciones: Optional[str] = None
    motivo_anulacion: Optional[str] = Field(None, max_length=500)
    fecha_anulacion: Optional[datetime] = None


class OrdenCompraRead(BaseModel):
    orden_compra_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    numero_oc: str
    fecha_emision: date
    fecha_requerida: date
    proveedor_id: UUID
    proveedor_razon_social: Optional[str] = None
    proveedor_ruc: Optional[str] = None
    almacen_destino_id: Optional[UUID] = None
    direccion_entrega: Optional[str] = None
    solicitud_compra_id: Optional[UUID] = None
    cotizacion_id: Optional[UUID] = None
    condicion_pago: str
    dias_credito: Optional[int] = None
    moneda: Optional[str] = None
    tipo_cambio: Optional[Decimal] = None
    subtotal: Optional[Decimal] = None
    descuento_global: Optional[Decimal] = None
    igv: Optional[Decimal] = None
    total: Optional[Decimal] = None
    total_items: Optional[int] = None
    items_recepcionados: Optional[int] = None
    porcentaje_recepcion: Optional[Decimal] = None
    estado: str
    requiere_aprobacion: Optional[bool] = None
    aprobado_por_usuario_id: Optional[UUID] = None
    fecha_aprobacion: Optional[datetime] = None
    centro_costo_id: Optional[UUID] = None
    observaciones: Optional[str] = None
    terminos_condiciones: Optional[str] = None
    motivo_anulacion: Optional[str] = None
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None
    fecha_anulacion: Optional[datetime] = None
    usuario_creacion_id: Optional[UUID] = None
    usuario_aprobacion_id: Optional[UUID] = None

    class Config:
        from_attributes = True


# ============================================================================
# RECEPCIÓN
# ============================================================================
class RecepcionCreate(BaseModel):
    empresa_id: UUID
    numero_recepcion: str = Field(..., max_length=20)
    fecha_recepcion: Optional[datetime] = None
    orden_compra_id: UUID
    proveedor_id: UUID
    almacen_id: UUID
    guia_remision_numero: Optional[str] = Field(None, max_length=30)
    guia_remision_fecha: Optional[date] = None
    transportista: Optional[str] = Field(None, max_length=150)
    placa_vehiculo: Optional[str] = Field(None, max_length=15)
    recepcionado_por_usuario_id: Optional[UUID] = None
    recepcionado_por_nombre: Optional[str] = Field(None, max_length=150)
    total_items: Optional[int] = 0
    total_cantidad: Optional[Decimal] = Field(0, ge=0)
    estado: Optional[str] = Field("borrador", max_length=20)
    requiere_inspeccion: Optional[bool] = False
    inspeccion_id: Optional[UUID] = None
    movimiento_inventario_id: Optional[UUID] = None
    observaciones: Optional[str] = None
    incidencias: Optional[str] = None


class RecepcionUpdate(BaseModel):
    numero_recepcion: Optional[str] = Field(None, max_length=20)
    fecha_recepcion: Optional[datetime] = None
    orden_compra_id: Optional[UUID] = None
    proveedor_id: Optional[UUID] = None
    almacen_id: Optional[UUID] = None
    guia_remision_numero: Optional[str] = Field(None, max_length=30)
    guia_remision_fecha: Optional[date] = None
    transportista: Optional[str] = Field(None, max_length=150)
    placa_vehiculo: Optional[str] = Field(None, max_length=15)
    recepcionado_por_usuario_id: Optional[UUID] = None
    recepcionado_por_nombre: Optional[str] = Field(None, max_length=150)
    total_items: Optional[int] = None
    total_cantidad: Optional[Decimal] = None
    estado: Optional[str] = Field(None, max_length=20)
    requiere_inspeccion: Optional[bool] = None
    inspeccion_id: Optional[UUID] = None
    movimiento_inventario_id: Optional[UUID] = None
    observaciones: Optional[str] = None
    incidencias: Optional[str] = None
    fecha_procesado: Optional[datetime] = None
    usuario_procesado_id: Optional[UUID] = None


class RecepcionRead(BaseModel):
    recepcion_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    numero_recepcion: str
    fecha_recepcion: datetime
    orden_compra_id: UUID
    proveedor_id: UUID
    almacen_id: UUID
    guia_remision_numero: Optional[str] = None
    guia_remision_fecha: Optional[date] = None
    transportista: Optional[str] = None
    placa_vehiculo: Optional[str] = None
    recepcionado_por_usuario_id: Optional[UUID] = None
    recepcionado_por_nombre: Optional[str] = None
    total_items: Optional[int] = None
    total_cantidad: Optional[Decimal] = None
    estado: str
    requiere_inspeccion: Optional[bool] = None
    inspeccion_id: Optional[UUID] = None
    movimiento_inventario_id: Optional[UUID] = None
    observaciones: Optional[str] = None
    incidencias: Optional[str] = None
    fecha_creacion: Optional[datetime] = None
    fecha_procesado: Optional[datetime] = None
    usuario_creacion_id: Optional[UUID] = None
    usuario_procesado_id: Optional[UUID] = None

    class Config:
        from_attributes = True
