# app/modules/log/presentation/schemas.py
"""
Schemas Pydantic para el módulo LOG (Logística y Distribución).
Todos los Create/Update excluyen cliente_id; se asigna desde contexto en backend.
✅ Campos esenciales incluidos desde el inicio.
"""
from typing import Optional
from uuid import UUID
from datetime import datetime, date, time
from decimal import Decimal
from pydantic import BaseModel, Field


# ============================================================================
# TRANSPORTISTA
# ============================================================================
class TransportistaCreate(BaseModel):
    empresa_id: UUID
    codigo_transportista: str = Field(..., max_length=20)
    razon_social: str = Field(..., max_length=200)
    nombre_comercial: Optional[str] = Field(None, max_length=150)
    tipo_documento: Optional[str] = Field("RUC", max_length=10)
    numero_documento: str = Field(..., max_length=20)
    numero_mtc: Optional[str] = Field(None, max_length=30)
    licencia_tipo: Optional[str] = Field(None, max_length=50)
    telefono: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    direccion: Optional[str] = Field(None, max_length=255)
    tarifa_km: Optional[Decimal] = Field(None, ge=0)
    tarifa_hora: Optional[Decimal] = Field(None, ge=0)
    moneda_tarifa: Optional[str] = Field("PEN", max_length=3)
    calificacion: Optional[Decimal] = Field(None, ge=0, le=5)
    es_activo: Optional[bool] = True


class TransportistaUpdate(BaseModel):
    codigo_transportista: Optional[str] = Field(None, max_length=20)
    razon_social: Optional[str] = Field(None, max_length=200)
    nombre_comercial: Optional[str] = Field(None, max_length=150)
    tipo_documento: Optional[str] = Field(None, max_length=10)
    numero_documento: Optional[str] = Field(None, max_length=20)
    numero_mtc: Optional[str] = Field(None, max_length=30)
    licencia_tipo: Optional[str] = Field(None, max_length=50)
    telefono: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    direccion: Optional[str] = Field(None, max_length=255)
    tarifa_km: Optional[Decimal] = Field(None, ge=0)
    tarifa_hora: Optional[Decimal] = Field(None, ge=0)
    moneda_tarifa: Optional[str] = Field(None, max_length=3)
    calificacion: Optional[Decimal] = Field(None, ge=0, le=5)
    es_activo: Optional[bool] = None


class TransportistaRead(BaseModel):
    transportista_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    codigo_transportista: str
    razon_social: str
    nombre_comercial: Optional[str]
    tipo_documento: Optional[str]
    numero_documento: str
    numero_mtc: Optional[str]
    licencia_tipo: Optional[str]
    telefono: Optional[str]
    email: Optional[str]
    direccion: Optional[str]
    tarifa_km: Optional[Decimal]
    tarifa_hora: Optional[Decimal]
    moneda_tarifa: Optional[str]
    calificacion: Optional[Decimal]
    es_activo: bool
    fecha_creacion: datetime
    usuario_creacion_id: Optional[UUID]

    class Config:
        from_attributes = True


# ============================================================================
# VEHÍCULO
# ============================================================================
class VehiculoCreate(BaseModel):
    empresa_id: UUID
    placa: str = Field(..., max_length=15)
    marca: Optional[str] = Field(None, max_length=50)
    modelo: Optional[str] = Field(None, max_length=50)
    año: Optional[int] = None
    color: Optional[str] = Field(None, max_length=30)
    tipo_vehiculo: str = Field(..., max_length=30)  # 'camion', 'camioneta', 'furgon', 'moto', 'trailer'
    categoria_vehiculo: Optional[str] = Field(None, max_length=20)  # 'ligero', 'mediano', 'pesado'
    capacidad_kg: Optional[Decimal] = Field(None, ge=0)
    capacidad_m3: Optional[Decimal] = Field(None, ge=0)
    tipo_propiedad: str = Field(..., max_length=20)  # 'propio', 'tercero'
    transportista_id: Optional[UUID] = None
    conductor_nombre: Optional[str] = Field(None, max_length=150)
    conductor_licencia: Optional[str] = Field(None, max_length=20)
    conductor_telefono: Optional[str] = Field(None, max_length=20)
    tarjeta_propiedad: Optional[str] = Field(None, max_length=30)
    soat_numero: Optional[str] = Field(None, max_length=30)
    soat_vencimiento: Optional[date] = None
    revision_tecnica_vencimiento: Optional[date] = None
    tiene_gps: Optional[bool] = False
    codigo_gps: Optional[str] = Field(None, max_length=50)
    estado_vehiculo: Optional[str] = Field("disponible", max_length=20)
    es_activo: Optional[bool] = True


class VehiculoUpdate(BaseModel):
    placa: Optional[str] = Field(None, max_length=15)
    marca: Optional[str] = Field(None, max_length=50)
    modelo: Optional[str] = Field(None, max_length=50)
    año: Optional[int] = None
    color: Optional[str] = Field(None, max_length=30)
    tipo_vehiculo: Optional[str] = Field(None, max_length=30)
    categoria_vehiculo: Optional[str] = Field(None, max_length=20)
    capacidad_kg: Optional[Decimal] = Field(None, ge=0)
    capacidad_m3: Optional[Decimal] = Field(None, ge=0)
    tipo_propiedad: Optional[str] = Field(None, max_length=20)
    transportista_id: Optional[UUID] = None
    conductor_nombre: Optional[str] = Field(None, max_length=150)
    conductor_licencia: Optional[str] = Field(None, max_length=20)
    conductor_telefono: Optional[str] = Field(None, max_length=20)
    tarjeta_propiedad: Optional[str] = Field(None, max_length=30)
    soat_numero: Optional[str] = Field(None, max_length=30)
    soat_vencimiento: Optional[date] = None
    revision_tecnica_vencimiento: Optional[date] = None
    tiene_gps: Optional[bool] = None
    codigo_gps: Optional[str] = Field(None, max_length=50)
    estado_vehiculo: Optional[str] = Field(None, max_length=20)
    es_activo: Optional[bool] = None


class VehiculoRead(BaseModel):
    vehiculo_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    placa: str
    marca: Optional[str]
    modelo: Optional[str]
    año: Optional[int]
    color: Optional[str]
    tipo_vehiculo: str
    categoria_vehiculo: Optional[str]
    capacidad_kg: Optional[Decimal]
    capacidad_m3: Optional[Decimal]
    tipo_propiedad: str
    transportista_id: Optional[UUID]
    conductor_nombre: Optional[str]
    conductor_licencia: Optional[str]
    conductor_telefono: Optional[str]
    tarjeta_propiedad: Optional[str]
    soat_numero: Optional[str]
    soat_vencimiento: Optional[date]
    revision_tecnica_vencimiento: Optional[date]
    tiene_gps: Optional[bool]
    codigo_gps: Optional[str]
    estado_vehiculo: Optional[str]
    es_activo: bool
    fecha_creacion: datetime
    usuario_creacion_id: Optional[UUID]

    class Config:
        from_attributes = True


# ============================================================================
# RUTA
# ============================================================================
class RutaCreate(BaseModel):
    empresa_id: UUID
    codigo_ruta: str = Field(..., max_length=20)
    nombre_ruta: str = Field(..., max_length=100)
    origen_sucursal_id: Optional[UUID] = None
    origen_descripcion: Optional[str] = Field(None, max_length=255)
    destino_descripcion: Optional[str] = Field(None, max_length=255)
    departamento_origen: Optional[str] = Field(None, max_length=50)
    departamento_destino: Optional[str] = Field(None, max_length=50)
    distancia_km: Optional[Decimal] = Field(None, ge=0)
    tiempo_estimado_horas: Optional[Decimal] = Field(None, ge=0)
    tipo_carretera: Optional[str] = Field(None, max_length=30)
    costo_estimado: Optional[Decimal] = Field(None, ge=0)
    moneda: Optional[str] = Field("PEN", max_length=3)
    cantidad_peajes: Optional[int] = Field(0, ge=0)
    costo_peajes: Optional[Decimal] = Field(0, ge=0)
    puntos_intermedios: Optional[str] = None  # JSON string
    es_activo: Optional[bool] = True


class RutaUpdate(BaseModel):
    codigo_ruta: Optional[str] = Field(None, max_length=20)
    nombre_ruta: Optional[str] = Field(None, max_length=100)
    origen_sucursal_id: Optional[UUID] = None
    origen_descripcion: Optional[str] = Field(None, max_length=255)
    destino_descripcion: Optional[str] = Field(None, max_length=255)
    departamento_origen: Optional[str] = Field(None, max_length=50)
    departamento_destino: Optional[str] = Field(None, max_length=50)
    distancia_km: Optional[Decimal] = Field(None, ge=0)
    tiempo_estimado_horas: Optional[Decimal] = Field(None, ge=0)
    tipo_carretera: Optional[str] = Field(None, max_length=30)
    costo_estimado: Optional[Decimal] = Field(None, ge=0)
    moneda: Optional[str] = Field(None, max_length=3)
    cantidad_peajes: Optional[int] = Field(None, ge=0)
    costo_peajes: Optional[Decimal] = Field(None, ge=0)
    puntos_intermedios: Optional[str] = None
    es_activo: Optional[bool] = None


class RutaRead(BaseModel):
    ruta_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    codigo_ruta: str
    nombre_ruta: str
    origen_sucursal_id: Optional[UUID]
    origen_descripcion: Optional[str]
    destino_descripcion: Optional[str]
    departamento_origen: Optional[str]
    departamento_destino: Optional[str]
    distancia_km: Optional[Decimal]
    tiempo_estimado_horas: Optional[Decimal]
    tipo_carretera: Optional[str]
    costo_estimado: Optional[Decimal]
    moneda: Optional[str]
    cantidad_peajes: Optional[int]
    costo_peajes: Optional[Decimal]
    puntos_intermedios: Optional[str]
    es_activo: bool
    fecha_creacion: datetime
    usuario_creacion_id: Optional[UUID]

    class Config:
        from_attributes = True


# ============================================================================
# GUÍA DE REMISIÓN
# ============================================================================
class GuiaRemisionCreate(BaseModel):
    empresa_id: UUID
    serie: str = Field(..., max_length=4)
    numero: str = Field(..., max_length=10)
    fecha_emision: Optional[date] = None
    fecha_traslado: date
    tipo_guia: str = Field(..., max_length=30)  # 'remitente', 'transportista'
    motivo_traslado: str = Field(..., max_length=30)  # 'venta', 'compra', 'transferencia', 'consignacion', 'devolucion'
    remitente_razon_social: str = Field(..., max_length=200)
    remitente_ruc: str = Field(..., max_length=11)
    remitente_direccion: Optional[str] = Field(None, max_length=255)
    destinatario_razon_social: str = Field(..., max_length=200)
    destinatario_documento_tipo: Optional[str] = Field(None, max_length=10)
    destinatario_documento_numero: Optional[str] = Field(None, max_length=20)
    destinatario_direccion: Optional[str] = Field(None, max_length=255)
    punto_partida: str = Field(..., max_length=255)
    punto_partida_ubigeo: Optional[str] = Field(None, max_length=6)
    punto_llegada: str = Field(..., max_length=255)
    punto_llegada_ubigeo: Optional[str] = Field(None, max_length=6)
    modalidad_transporte: str = Field(..., max_length=20)  # 'publico', 'privado'
    transportista_id: Optional[UUID] = None
    transportista_razon_social: Optional[str] = Field(None, max_length=200)
    transportista_ruc: Optional[str] = Field(None, max_length=11)
    vehiculo_id: Optional[UUID] = None
    vehiculo_placa: Optional[str] = Field(None, max_length=15)
    conductor_nombre: Optional[str] = Field(None, max_length=150)
    conductor_documento_tipo: Optional[str] = Field(None, max_length=10)
    conductor_documento_numero: Optional[str] = Field(None, max_length=20)
    conductor_licencia: Optional[str] = Field(None, max_length=20)
    total_bultos: Optional[int] = Field(0, ge=0)
    peso_total_kg: Optional[Decimal] = Field(0, ge=0)
    documento_sustento_tipo: Optional[str] = Field(None, max_length=20)
    documento_sustento_serie: Optional[str] = Field(None, max_length=4)
    documento_sustento_numero: Optional[str] = Field(None, max_length=10)
    movimiento_inventario_id: Optional[UUID] = None
    venta_id: Optional[UUID] = None
    estado: Optional[str] = Field("emitida", max_length=20)
    fecha_entrega: Optional[datetime] = None
    codigo_hash: Optional[str] = Field(None, max_length=100)
    codigo_qr: Optional[str] = None
    observaciones: Optional[str] = None


class GuiaRemisionUpdate(BaseModel):
    serie: Optional[str] = Field(None, max_length=4)
    numero: Optional[str] = Field(None, max_length=10)
    fecha_emision: Optional[date] = None
    fecha_traslado: Optional[date] = None
    tipo_guia: Optional[str] = Field(None, max_length=30)
    motivo_traslado: Optional[str] = Field(None, max_length=30)
    remitente_razon_social: Optional[str] = Field(None, max_length=200)
    remitente_ruc: Optional[str] = Field(None, max_length=11)
    remitente_direccion: Optional[str] = Field(None, max_length=255)
    destinatario_razon_social: Optional[str] = Field(None, max_length=200)
    destinatario_documento_tipo: Optional[str] = Field(None, max_length=10)
    destinatario_documento_numero: Optional[str] = Field(None, max_length=20)
    destinatario_direccion: Optional[str] = Field(None, max_length=255)
    punto_partida: Optional[str] = Field(None, max_length=255)
    punto_partida_ubigeo: Optional[str] = Field(None, max_length=6)
    punto_llegada: Optional[str] = Field(None, max_length=255)
    punto_llegada_ubigeo: Optional[str] = Field(None, max_length=6)
    modalidad_transporte: Optional[str] = Field(None, max_length=20)
    transportista_id: Optional[UUID] = None
    transportista_razon_social: Optional[str] = Field(None, max_length=200)
    transportista_ruc: Optional[str] = Field(None, max_length=11)
    vehiculo_id: Optional[UUID] = None
    vehiculo_placa: Optional[str] = Field(None, max_length=15)
    conductor_nombre: Optional[str] = Field(None, max_length=150)
    conductor_documento_tipo: Optional[str] = Field(None, max_length=10)
    conductor_documento_numero: Optional[str] = Field(None, max_length=20)
    conductor_licencia: Optional[str] = Field(None, max_length=20)
    total_bultos: Optional[int] = Field(None, ge=0)
    peso_total_kg: Optional[Decimal] = Field(None, ge=0)
    documento_sustento_tipo: Optional[str] = Field(None, max_length=20)
    documento_sustento_serie: Optional[str] = Field(None, max_length=4)
    documento_sustento_numero: Optional[str] = Field(None, max_length=10)
    movimiento_inventario_id: Optional[UUID] = None
    venta_id: Optional[UUID] = None
    estado: Optional[str] = Field(None, max_length=20)
    fecha_entrega: Optional[datetime] = None
    codigo_hash: Optional[str] = Field(None, max_length=100)
    codigo_qr: Optional[str] = None
    observaciones: Optional[str] = None


class GuiaRemisionRead(BaseModel):
    guia_remision_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    serie: str
    numero: str
    fecha_emision: date
    fecha_traslado: date
    tipo_guia: str
    motivo_traslado: str
    remitente_razon_social: str
    remitente_ruc: str
    remitente_direccion: Optional[str]
    destinatario_razon_social: str
    destinatario_documento_tipo: Optional[str]
    destinatario_documento_numero: Optional[str]
    destinatario_direccion: Optional[str]
    punto_partida: str
    punto_partida_ubigeo: Optional[str]
    punto_llegada: str
    punto_llegada_ubigeo: Optional[str]
    modalidad_transporte: str
    transportista_id: Optional[UUID]
    transportista_razon_social: Optional[str]
    transportista_ruc: Optional[str]
    vehiculo_id: Optional[UUID]
    vehiculo_placa: Optional[str]
    conductor_nombre: Optional[str]
    conductor_documento_tipo: Optional[str]
    conductor_documento_numero: Optional[str]
    conductor_licencia: Optional[str]
    total_bultos: Optional[int]
    peso_total_kg: Optional[Decimal]
    documento_sustento_tipo: Optional[str]
    documento_sustento_serie: Optional[str]
    documento_sustento_numero: Optional[str]
    movimiento_inventario_id: Optional[UUID]
    venta_id: Optional[UUID]
    estado: str
    fecha_entrega: Optional[datetime]
    codigo_hash: Optional[str]
    codigo_qr: Optional[str]
    observaciones: Optional[str]
    fecha_creacion: datetime
    fecha_anulacion: Optional[datetime]
    usuario_creacion_id: Optional[UUID]

    class Config:
        from_attributes = True


# ============================================================================
# GUÍA DE REMISIÓN DETALLE
# ============================================================================
class GuiaRemisionDetalleCreate(BaseModel):
    guia_remision_id: UUID
    producto_id: UUID
    cantidad: Decimal = Field(..., ge=0)
    unidad_medida_id: UUID
    descripcion: Optional[str] = Field(None, max_length=255)
    peso_kg: Optional[Decimal] = Field(None, ge=0)


class GuiaRemisionDetalleUpdate(BaseModel):
    producto_id: Optional[UUID] = None
    cantidad: Optional[Decimal] = Field(None, ge=0)
    unidad_medida_id: Optional[UUID] = None
    descripcion: Optional[str] = Field(None, max_length=255)
    peso_kg: Optional[Decimal] = Field(None, ge=0)


class GuiaRemisionDetalleRead(BaseModel):
    guia_detalle_id: UUID
    cliente_id: UUID
    guia_remision_id: UUID
    producto_id: UUID
    cantidad: Decimal
    unidad_medida_id: UUID
    descripcion: Optional[str]
    peso_kg: Optional[Decimal]
    fecha_creacion: datetime

    class Config:
        from_attributes = True


# ============================================================================
# DESPACHO
# ============================================================================
class DespachoCreate(BaseModel):
    empresa_id: UUID
    numero_despacho: str = Field(..., max_length=20)
    fecha_programada: date
    hora_salida_programada: Optional[time] = None
    ruta_id: Optional[UUID] = None
    origen_sucursal_id: Optional[UUID] = None
    vehiculo_id: Optional[UUID] = None
    conductor_nombre: Optional[str] = Field(None, max_length=150)
    conductor_telefono: Optional[str] = Field(None, max_length=20)
    fecha_salida_real: Optional[datetime] = None
    fecha_retorno: Optional[datetime] = None
    km_inicial: Optional[Decimal] = Field(None, ge=0)
    km_final: Optional[Decimal] = Field(None, ge=0)
    total_guias: Optional[int] = Field(0, ge=0)
    total_peso_kg: Optional[Decimal] = Field(0, ge=0)
    total_bultos: Optional[int] = Field(0, ge=0)
    costo_combustible: Optional[Decimal] = Field(None, ge=0)
    costo_peajes: Optional[Decimal] = Field(None, ge=0)
    otros_gastos: Optional[Decimal] = Field(None, ge=0)
    estado: Optional[str] = Field("planificado", max_length=20)
    observaciones: Optional[str] = None
    incidencias: Optional[str] = None


class DespachoUpdate(BaseModel):
    numero_despacho: Optional[str] = Field(None, max_length=20)
    fecha_programada: Optional[date] = None
    hora_salida_programada: Optional[time] = None
    ruta_id: Optional[UUID] = None
    origen_sucursal_id: Optional[UUID] = None
    vehiculo_id: Optional[UUID] = None
    conductor_nombre: Optional[str] = Field(None, max_length=150)
    conductor_telefono: Optional[str] = Field(None, max_length=20)
    fecha_salida_real: Optional[datetime] = None
    fecha_retorno: Optional[datetime] = None
    km_inicial: Optional[Decimal] = Field(None, ge=0)
    km_final: Optional[Decimal] = Field(None, ge=0)
    total_guias: Optional[int] = Field(None, ge=0)
    total_peso_kg: Optional[Decimal] = Field(None, ge=0)
    total_bultos: Optional[int] = Field(None, ge=0)
    costo_combustible: Optional[Decimal] = Field(None, ge=0)
    costo_peajes: Optional[Decimal] = Field(None, ge=0)
    otros_gastos: Optional[Decimal] = Field(None, ge=0)
    estado: Optional[str] = Field(None, max_length=20)
    observaciones: Optional[str] = None
    incidencias: Optional[str] = None


class DespachoRead(BaseModel):
    despacho_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    numero_despacho: str
    fecha_programada: date
    hora_salida_programada: Optional[time]
    ruta_id: Optional[UUID]
    origen_sucursal_id: Optional[UUID]
    vehiculo_id: Optional[UUID]
    conductor_nombre: Optional[str]
    conductor_telefono: Optional[str]
    fecha_salida_real: Optional[datetime]
    fecha_retorno: Optional[datetime]
    km_inicial: Optional[Decimal]
    km_final: Optional[Decimal]
    total_guias: Optional[int]
    total_peso_kg: Optional[Decimal]
    total_bultos: Optional[int]
    costo_combustible: Optional[Decimal]
    costo_peajes: Optional[Decimal]
    otros_gastos: Optional[Decimal]
    estado: str
    observaciones: Optional[str]
    incidencias: Optional[str]
    fecha_creacion: datetime
    usuario_creacion_id: Optional[UUID]

    class Config:
        from_attributes = True


# ============================================================================
# DESPACHO-GUÍA
# ============================================================================
class DespachoGuiaCreate(BaseModel):
    despacho_id: UUID
    guia_remision_id: UUID
    orden_entrega: Optional[int] = Field(None, ge=0)
    fecha_entrega: Optional[datetime] = None
    estado_entrega: Optional[str] = Field("pendiente", max_length=20)
    observaciones_entrega: Optional[str] = Field(None, max_length=500)
    receptor_nombre: Optional[str] = Field(None, max_length=150)
    receptor_documento: Optional[str] = Field(None, max_length=20)


class DespachoGuiaUpdate(BaseModel):
    despacho_id: Optional[UUID] = None
    guia_remision_id: Optional[UUID] = None
    orden_entrega: Optional[int] = Field(None, ge=0)
    fecha_entrega: Optional[datetime] = None
    estado_entrega: Optional[str] = Field(None, max_length=20)
    observaciones_entrega: Optional[str] = Field(None, max_length=500)
    receptor_nombre: Optional[str] = Field(None, max_length=150)
    receptor_documento: Optional[str] = Field(None, max_length=20)


class DespachoGuiaRead(BaseModel):
    despacho_guia_id: UUID
    cliente_id: UUID
    despacho_id: UUID
    guia_remision_id: UUID
    orden_entrega: Optional[int]
    fecha_entrega: Optional[datetime]
    estado_entrega: Optional[str]
    observaciones_entrega: Optional[str]
    receptor_nombre: Optional[str]
    receptor_documento: Optional[str]
    fecha_creacion: datetime

    class Config:
        from_attributes = True
