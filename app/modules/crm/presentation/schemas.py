# app/modules/crm/presentation/schemas.py
"""
Schemas Pydantic para el módulo CRM (Customer Relationship Management).
Todos los Create/Update excluyen cliente_id; se asigna desde contexto en backend.
✅ Campos esenciales incluidos desde el inicio.
"""
from typing import Optional
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field


# ============================================================================
# CAMPAÑA
# ============================================================================
class CampanaCreate(BaseModel):
    empresa_id: UUID
    codigo_campana: str = Field(..., max_length=20)
    nombre: str = Field(..., max_length=150)
    descripcion: Optional[str] = Field(None, max_length=500)
    tipo_campana: str = Field(..., max_length=30)  # 'email', 'telemarketing', 'evento', 'digital', 'mixta'
    objetivo: Optional[str] = Field(None, max_length=500)
    fecha_inicio: date
    fecha_fin: Optional[date] = None
    presupuesto: Optional[Decimal] = Field(None, ge=0)
    gasto_real: Optional[Decimal] = Field(0, ge=0)
    moneda: Optional[str] = Field("PEN", max_length=3)
    responsable_usuario_id: Optional[UUID] = None
    responsable_nombre: Optional[str] = Field(None, max_length=150)
    estado: Optional[str] = Field("planificada", max_length=20)
    observaciones: Optional[str] = None


class CampanaUpdate(BaseModel):
    codigo_campana: Optional[str] = Field(None, max_length=20)
    nombre: Optional[str] = Field(None, max_length=150)
    descripcion: Optional[str] = Field(None, max_length=500)
    tipo_campana: Optional[str] = Field(None, max_length=30)
    objetivo: Optional[str] = Field(None, max_length=500)
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    presupuesto: Optional[Decimal] = Field(None, ge=0)
    gasto_real: Optional[Decimal] = Field(None, ge=0)
    moneda: Optional[str] = Field(None, max_length=3)
    responsable_usuario_id: Optional[UUID] = None
    responsable_nombre: Optional[str] = Field(None, max_length=150)
    total_contactos: Optional[int] = Field(None, ge=0)
    total_leads_generados: Optional[int] = Field(None, ge=0)
    total_oportunidades: Optional[int] = Field(None, ge=0)
    total_ventas_cerradas: Optional[int] = Field(None, ge=0)
    monto_ventas_cerradas: Optional[Decimal] = Field(None, ge=0)
    estado: Optional[str] = Field(None, max_length=20)
    observaciones: Optional[str] = None


class CampanaRead(BaseModel):
    campana_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    codigo_campana: str
    nombre: str
    descripcion: Optional[str]
    tipo_campana: str
    objetivo: Optional[str]
    fecha_inicio: date
    fecha_fin: Optional[date]
    presupuesto: Optional[Decimal]
    gasto_real: Optional[Decimal]
    moneda: Optional[str]
    responsable_usuario_id: Optional[UUID]
    responsable_nombre: Optional[str]
    total_contactos: Optional[int]
    total_leads_generados: Optional[int]
    total_oportunidades: Optional[int]
    total_ventas_cerradas: Optional[int]
    monto_ventas_cerradas: Optional[Decimal]
    estado: Optional[str]
    observaciones: Optional[str]
    fecha_creacion: datetime
    usuario_creacion_id: Optional[UUID]

    class Config:
        from_attributes = True


# ============================================================================
# LEAD
# ============================================================================
class LeadCreate(BaseModel):
    empresa_id: UUID
    nombre_completo: str = Field(..., max_length=200)
    empresa_nombre: Optional[str] = Field(None, max_length=200)
    cargo: Optional[str] = Field(None, max_length=100)
    telefono: Optional[str] = Field(None, max_length=20)
    telefono_movil: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    direccion: Optional[str] = Field(None, max_length=255)
    ciudad: Optional[str] = Field(None, max_length=100)
    pais: Optional[str] = Field("Perú", max_length=50)
    origen_lead: str = Field(..., max_length=30)  # 'web', 'telefono', 'referido', 'evento', 'campana', 'redes_sociales'
    campana_id: Optional[UUID] = None
    referido_por: Optional[str] = Field(None, max_length=150)
    calificacion: Optional[str] = Field("frio", max_length=20)  # 'caliente', 'tibio', 'frio'
    puntuacion: Optional[int] = Field(0, ge=0, le=100)
    asignado_vendedor_usuario_id: Optional[UUID] = None
    asignado_vendedor_nombre: Optional[str] = Field(None, max_length=150)
    estado: Optional[str] = Field("nuevo", max_length=20)
    observaciones: Optional[str] = None


class LeadUpdate(BaseModel):
    nombre_completo: Optional[str] = Field(None, max_length=200)
    empresa_nombre: Optional[str] = Field(None, max_length=200)
    cargo: Optional[str] = Field(None, max_length=100)
    telefono: Optional[str] = Field(None, max_length=20)
    telefono_movil: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    direccion: Optional[str] = Field(None, max_length=255)
    ciudad: Optional[str] = Field(None, max_length=100)
    pais: Optional[str] = Field(None, max_length=50)
    origen_lead: Optional[str] = Field(None, max_length=30)
    campana_id: Optional[UUID] = None
    referido_por: Optional[str] = Field(None, max_length=150)
    calificacion: Optional[str] = Field(None, max_length=20)
    puntuacion: Optional[int] = Field(None, ge=0, le=100)
    asignado_vendedor_usuario_id: Optional[UUID] = None
    asignado_vendedor_nombre: Optional[str] = Field(None, max_length=150)
    fecha_asignacion: Optional[datetime] = None
    estado: Optional[str] = Field(None, max_length=20)
    fecha_primer_contacto: Optional[datetime] = None
    fecha_ultimo_contacto: Optional[datetime] = None
    convertido_cliente: Optional[bool] = None
    cliente_venta_id: Optional[UUID] = None
    fecha_conversion: Optional[datetime] = None
    motivo_descarte: Optional[str] = Field(None, max_length=500)
    observaciones: Optional[str] = None


class LeadRead(BaseModel):
    lead_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    nombre_completo: str
    empresa_nombre: Optional[str]
    cargo: Optional[str]
    telefono: Optional[str]
    telefono_movil: Optional[str]
    email: Optional[str]
    direccion: Optional[str]
    ciudad: Optional[str]
    pais: Optional[str]
    origen_lead: str
    campana_id: Optional[UUID]
    referido_por: Optional[str]
    calificacion: Optional[str]
    puntuacion: Optional[int]
    asignado_vendedor_usuario_id: Optional[UUID]
    asignado_vendedor_nombre: Optional[str]
    fecha_asignacion: Optional[datetime]
    estado: Optional[str]
    fecha_primer_contacto: Optional[datetime]
    fecha_ultimo_contacto: Optional[datetime]
    convertido_cliente: Optional[bool]
    cliente_venta_id: Optional[UUID]
    fecha_conversion: Optional[datetime]
    motivo_descarte: Optional[str]
    observaciones: Optional[str]
    fecha_creacion: datetime
    usuario_creacion_id: Optional[UUID]

    class Config:
        from_attributes = True


# ============================================================================
# OPORTUNIDAD
# ============================================================================
class OportunidadCreate(BaseModel):
    empresa_id: UUID
    numero_oportunidad: str = Field(..., max_length=20)
    nombre: str = Field(..., max_length=200)
    descripcion: Optional[str] = None
    cliente_venta_id: Optional[UUID] = None
    lead_id: Optional[UUID] = None
    nombre_cliente_prospecto: Optional[str] = Field(None, max_length=200)
    vendedor_usuario_id: UUID
    vendedor_nombre: Optional[str] = Field(None, max_length=150)
    campana_id: Optional[UUID] = None
    monto_estimado: Decimal = Field(..., ge=0)
    moneda: Optional[str] = Field("PEN", max_length=3)
    probabilidad_cierre: Optional[Decimal] = Field(50, ge=0, le=100)
    fecha_apertura: Optional[date] = None
    fecha_cierre_estimada: Optional[date] = None
    etapa: str = Field(..., max_length=30)  # 'calificacion', 'necesidad_analisis', 'propuesta', 'negociacion', 'cierre'
    tipo_oportunidad: Optional[str] = Field(None, max_length=30)
    productos_interes: Optional[str] = None  # JSON string
    estado: Optional[str] = Field("abierta", max_length=20)
    observaciones: Optional[str] = None
    proxima_accion: Optional[str] = Field(None, max_length=500)
    fecha_proxima_accion: Optional[date] = None


class OportunidadUpdate(BaseModel):
    numero_oportunidad: Optional[str] = Field(None, max_length=20)
    nombre: Optional[str] = Field(None, max_length=200)
    descripcion: Optional[str] = None
    cliente_venta_id: Optional[UUID] = None
    lead_id: Optional[UUID] = None
    nombre_cliente_prospecto: Optional[str] = Field(None, max_length=200)
    vendedor_usuario_id: Optional[UUID] = None
    vendedor_nombre: Optional[str] = Field(None, max_length=150)
    campana_id: Optional[UUID] = None
    monto_estimado: Optional[Decimal] = Field(None, ge=0)
    moneda: Optional[str] = Field(None, max_length=3)
    probabilidad_cierre: Optional[Decimal] = Field(None, ge=0, le=100)
    fecha_apertura: Optional[date] = None
    fecha_cierre_estimada: Optional[date] = None
    fecha_cierre_real: Optional[date] = None
    etapa: Optional[str] = Field(None, max_length=30)
    etapa_anterior: Optional[str] = Field(None, max_length=30)
    fecha_cambio_etapa: Optional[datetime] = None
    tipo_oportunidad: Optional[str] = Field(None, max_length=30)
    productos_interes: Optional[str] = None
    estado: Optional[str] = Field(None, max_length=20)
    motivo_ganada: Optional[str] = Field(None, max_length=500)
    motivo_perdida: Optional[str] = Field(None, max_length=500)
    competidor: Optional[str] = Field(None, max_length=150)
    cotizacion_generada: Optional[bool] = None
    cotizacion_id: Optional[UUID] = None
    pedido_generado: Optional[bool] = None
    pedido_id: Optional[UUID] = None
    observaciones: Optional[str] = None
    proxima_accion: Optional[str] = Field(None, max_length=500)
    fecha_proxima_accion: Optional[date] = None


class OportunidadRead(BaseModel):
    oportunidad_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    numero_oportunidad: str
    nombre: str
    descripcion: Optional[str]
    cliente_venta_id: Optional[UUID]
    lead_id: Optional[UUID]
    nombre_cliente_prospecto: Optional[str]
    vendedor_usuario_id: UUID
    vendedor_nombre: Optional[str]
    campana_id: Optional[UUID]
    monto_estimado: Decimal
    moneda: Optional[str]
    probabilidad_cierre: Optional[Decimal]
    fecha_apertura: date
    fecha_cierre_estimada: Optional[date]
    fecha_cierre_real: Optional[date]
    etapa: str
    etapa_anterior: Optional[str]
    fecha_cambio_etapa: Optional[datetime]
    tipo_oportunidad: Optional[str]
    productos_interes: Optional[str]
    estado: Optional[str]
    motivo_ganada: Optional[str]
    motivo_perdida: Optional[str]
    competidor: Optional[str]
    cotizacion_generada: Optional[bool]
    cotizacion_id: Optional[UUID]
    pedido_generado: Optional[bool]
    pedido_id: Optional[UUID]
    observaciones: Optional[str]
    proxima_accion: Optional[str]
    fecha_proxima_accion: Optional[date]
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime]
    usuario_creacion_id: Optional[UUID]

    class Config:
        from_attributes = True


# ============================================================================
# ACTIVIDAD
# ============================================================================
class ActividadCreate(BaseModel):
    empresa_id: UUID
    tipo_actividad: str = Field(..., max_length=30)  # 'llamada', 'reunion', 'email', 'visita', 'demo', 'cotizacion_enviada'
    asunto: str = Field(..., max_length=200)
    descripcion: Optional[str] = None
    lead_id: Optional[UUID] = None
    oportunidad_id: Optional[UUID] = None
    cliente_venta_id: Optional[UUID] = None
    fecha_actividad: datetime
    duracion_minutos: Optional[int] = Field(None, ge=0)
    usuario_responsable_id: UUID
    responsable_nombre: Optional[str] = Field(None, max_length=150)
    resultado: Optional[str] = Field(None, max_length=30)
    requiere_seguimiento: Optional[bool] = False
    fecha_seguimiento: Optional[date] = None
    estado: Optional[str] = Field("planificada", max_length=20)
    observaciones: Optional[str] = None


class ActividadUpdate(BaseModel):
    tipo_actividad: Optional[str] = Field(None, max_length=30)
    asunto: Optional[str] = Field(None, max_length=200)
    descripcion: Optional[str] = None
    lead_id: Optional[UUID] = None
    oportunidad_id: Optional[UUID] = None
    cliente_venta_id: Optional[UUID] = None
    fecha_actividad: Optional[datetime] = None
    duracion_minutos: Optional[int] = Field(None, ge=0)
    usuario_responsable_id: Optional[UUID] = None
    responsable_nombre: Optional[str] = Field(None, max_length=150)
    resultado: Optional[str] = Field(None, max_length=30)
    requiere_seguimiento: Optional[bool] = None
    fecha_seguimiento: Optional[date] = None
    estado: Optional[str] = Field(None, max_length=20)
    fecha_completado: Optional[datetime] = None
    observaciones: Optional[str] = None


class ActividadRead(BaseModel):
    actividad_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    tipo_actividad: str
    asunto: str
    descripcion: Optional[str]
    lead_id: Optional[UUID]
    oportunidad_id: Optional[UUID]
    cliente_venta_id: Optional[UUID]
    fecha_actividad: datetime
    duracion_minutos: Optional[int]
    usuario_responsable_id: UUID
    responsable_nombre: Optional[str]
    resultado: Optional[str]
    requiere_seguimiento: Optional[bool]
    fecha_seguimiento: Optional[date]
    estado: Optional[str]
    fecha_completado: Optional[datetime]
    observaciones: Optional[str]
    fecha_creacion: datetime
    usuario_creacion_id: Optional[UUID]

    class Config:
        from_attributes = True
