# app/schemas/cliente.py
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field, EmailStr, validator, field_validator
import re
import json

class ClienteBase(BaseModel):
    """
    Esquema base para la entidad Cliente, alineado con la tabla de la BD multi-tenant.
    Contiene todos los campos principales de identificación, configuración y contacto.
    """
    # ========================================
    # IDENTIFICACIÓN Y BRANDING
    # ========================================
    codigo_cliente: str = Field(
        ..., 
        max_length=20, 
        description="Código corto único para identificar al cliente (ej: 'CLI001', 'ACME')."
    )
    subdominio: str = Field(
        ..., 
        max_length=63, 
        description="Subdominio único para acceso web (ej: 'acme' → acme.tuapp.com)."
    )
    razon_social: str = Field(
        ..., 
        max_length=200, 
        description="Nombre legal completo de la empresa."
    )
    nombre_comercial: Optional[str] = Field(
        None, 
        max_length=150, 
        description="Nombre corto para mostrar en la UI."
    )
    ruc: Optional[str] = Field(
        None, 
        max_length=11, 
        description="RUC del cliente (11 dígitos)."
    )

    # ========================================
    # CONFIGURACIÓN DE INSTALACIÓN
    # ========================================
    tipo_instalacion: str = Field(
        "cloud", 
        description="Tipo de instalación: 'cloud', 'onpremise', 'hybrid'."
    )
    servidor_api_local: Optional[str] = Field(
        None, 
        max_length=255, 
        description="URL del API si el cliente tiene instalación local."
    )

    # ========================================
    # AUTENTICACIÓN
    # ========================================
    modo_autenticacion: str = Field(
        "local", 
        description="Modo de autenticación: 'local', 'sso', 'hybrid'."
    )

    # ========================================
    # PERSONALIZACIÓN VISUAL (BRANDING)
    # ========================================
    logo_url: Optional[str] = Field(
        None, 
        max_length=500, 
        description="URL pública del logo del cliente."
    )
    favicon_url: Optional[str] = Field(
        None, 
        max_length=500, 
        description="URL del favicon personalizado."
    )
    color_primario: str = Field(
        "#1976D2", 
        description="Color principal en formato HEX (#RRGGBB)."
    )
    color_secundario: str = Field(
        "#424242", 
        description="Color secundario en formato HEX."
    )
    tema_personalizado: Optional[str] = Field(
        None, 
        description="JSON con configuración avanzada de tema."
    )

    # ========================================
    # ESTADO Y SUSCRIPCIÓN
    # ========================================
    plan_suscripcion: str = Field(
        "trial", 
        description="Plan contratado: 'trial', 'basico', 'profesional', 'enterprise'."
    )
    estado_suscripcion: str = Field(
        "activo", 
        description="Estado actual: 'trial', 'activo', 'suspendido', 'cancelado', 'moroso'."
    )
    fecha_inicio_suscripcion: Optional[date] = Field(
        None, 
        description="Fecha de inicio de la suscripción pagada."
    )
    fecha_fin_trial: Optional[date] = Field(
        None, 
        description="Fecha de fin del periodo de prueba."
    )

    # ========================================
    # CONTACTO PRINCIPAL
    # ========================================
    contacto_nombre: Optional[str] = Field(
        None, 
        max_length=100, 
        description="Nombre del contacto administrativo."
    )
    contacto_email: str = Field(
        ..., 
        description="Email del administrador principal (REQUERIDO)."
    )
    contacto_telefono: Optional[str] = Field(
        None, 
        max_length=20, 
        description="Teléfono de contacto."
    )

    # ========================================
    # CONTROL DE ESTADO
    # ========================================
    es_activo: bool = Field(
        True, 
        description="Si está inactivo, bloquea acceso a todos los usuarios del cliente."
    )
    es_demo: bool = Field(
        False, 
        description="Marca clientes de demostración (datos de prueba)."
    )

    # ========================================
    # METADATOS EXTENSIBLES
    # ========================================
    metadata_json: Optional[str] = Field(
        None, 
        description="JSON para configuraciones custom sin alterar schema."
    )

    # ========================================
    # SINCRONIZACIÓN MULTI-INSTALACIÓN
    # ========================================
    api_key_sincronizacion: Optional[str] = Field(
        None,
        max_length=255,
        description="API Key para sincronización con servidor central (multi-instalación)."
    )
    sincronizacion_habilitada: bool = Field(
        False,
        description="Habilita sincronización bidireccional con servidor central."
    )
    ultima_sincronizacion: Optional[datetime] = Field(
        None,
        description="Última fecha y hora de sincronización con servidor central."
    )

    # === VALIDADORES ===
    @validator('subdominio')
    def validar_subdominio(cls, v):
        if not re.match(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$", v):
            raise ValueError(
                "El subdominio debe contener solo letras minúsculas, números y guiones, "
                "y no puede comenzar o terminar con guión."
            )
        return v

    @validator('color_primario', 'color_secundario')
    def validar_color_hex(cls, v):
        if not re.match(r"^#[0-9A-Fa-f]{6}$", v):
            raise ValueError("El color debe estar en formato HEX válido (#RRGGBB).")
        return v

    @field_validator('contacto_email')
    @classmethod
    def validar_email_local(cls, v: str) -> str:
        if "@" not in v:
            raise ValueError("El email debe contener un @")
        return v
    
    @validator('tipo_instalacion')
    def validar_tipo_instalacion(cls, v):
        tipos_validos = ['cloud', 'onpremise', 'hybrid']
        if v not in tipos_validos:
            raise ValueError(f"tipo_instalacion debe ser uno de: {', '.join(tipos_validos)}")
        return v
    
    @validator('modo_autenticacion')
    def validar_modo_autenticacion(cls, v):
        modos_validos = ['local', 'sso', 'hybrid']
        if v not in modos_validos:
            raise ValueError(f"modo_autenticacion debe ser uno de: {', '.join(modos_validos)}")
        return v
    
    @validator('plan_suscripcion')
    def validar_plan_suscripcion(cls, v):
        planes_validos = ['trial', 'basico', 'profesional', 'enterprise']
        if v not in planes_validos:
            raise ValueError(f"plan_suscripcion debe ser uno de: {', '.join(planes_validos)}")
        return v
    
    @validator('estado_suscripcion')
    def validar_estado_suscripcion(cls, v):
        estados_validos = ['trial', 'activo', 'suspendido', 'cancelado', 'moroso']
        if v not in estados_validos:
            raise ValueError(f"estado_suscripcion debe ser uno de: {', '.join(estados_validos)}")
        return v
    
    @validator('ruc')
    def validar_ruc(cls, v):
        if v is not None and v.strip():
            # Validar que RUC sea numérico (ajustar según país)
            if not v.isdigit():
                raise ValueError("El RUC debe contener solo números")
            if len(v) < 8 or len(v) > 15:
                raise ValueError("El RUC debe tener entre 8 y 15 dígitos")
        return v
    
    @validator('tema_personalizado')
    def validar_tema_json(cls, v):
        if v is not None and v.strip():
            try:
                json.loads(v)
            except json.JSONDecodeError:
                raise ValueError("tema_personalizado debe ser un JSON válido")
        return v
    
    @validator('servidor_api_local')
    def validar_url_servidor(cls, v):
        if v is not None and v.strip():
            # Validación básica de URL
            if not (v.startswith('http://') or v.startswith('https://')):
                raise ValueError("servidor_api_local debe ser una URL válida (http:// o https://)")
        return v

    class Config:
        from_attributes = True


class ClienteCreate(ClienteBase):
    """Esquema para la creación de un nuevo cliente. Hereda todos los campos de ClienteBase."""
    pass


class ClienteUpdate(BaseModel):
    """
    Esquema para la actualización parcial de un cliente.
    Todos los campos son opcionales.
    """
    # Reutilizamos las mismas definiciones pero como opcionales
    codigo_cliente: Optional[str] = Field(None, max_length=20)
    subdominio: Optional[str] = Field(None, max_length=63)
    razon_social: Optional[str] = Field(None, max_length=200)
    nombre_comercial: Optional[str] = Field(None, max_length=150)
    ruc: Optional[str] = Field(None, max_length=15)
    tipo_instalacion: Optional[str] = None
    servidor_api_local: Optional[str] = Field(None, max_length=255)
    modo_autenticacion: Optional[str] = None
    logo_url: Optional[str] = Field(None, max_length=500)
    favicon_url: Optional[str] = Field(None, max_length=500)
    color_primario: Optional[str] = None
    color_secundario: Optional[str] = None
    tema_personalizado: Optional[str] = None
    plan_suscripcion: Optional[str] = None
    estado_suscripcion: Optional[str] = None
    fecha_inicio_suscripcion: Optional[date] = None
    fecha_fin_trial: Optional[date] = None
    contacto_nombre: Optional[str] = Field(None, max_length=100)
    contacto_email: Optional[EmailStr] = None
    contacto_telefono: Optional[str] = Field(None, max_length=20)
    es_activo: Optional[bool] = None
    es_demo: Optional[bool] = None
    metadata_json: Optional[str] = None
    api_key_sincronizacion: Optional[str] = Field(None, max_length=255)
    sincronizacion_habilitada: Optional[bool] = None
    ultima_sincronizacion: Optional[datetime] = None
    
    # Validadores para campos opcionales
    @validator('subdominio')
    def validar_subdominio_update(cls, v):
        if v is not None:
            if not re.match(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$", v):
                raise ValueError(
                    "El subdominio debe contener solo letras minúsculas, números y guiones, "
                    "y no puede comenzar o terminar con guión."
                )
        return v
    
    @validator('color_primario', 'color_secundario')
    def validar_color_hex_update(cls, v):
        if v is not None:
            if not re.match(r"^#[0-9A-Fa-f]{6}$", v):
                raise ValueError("El color debe estar en formato HEX válido (#RRGGBB).")
        return v
    
    @validator('tipo_instalacion')
    def validar_tipo_instalacion_update(cls, v):
        if v is not None:
            tipos_validos = ['cloud', 'onpremise', 'hybrid']
            if v not in tipos_validos:
                raise ValueError(f"tipo_instalacion debe ser uno de: {', '.join(tipos_validos)}")
        return v
    
    @validator('modo_autenticacion')
    def validar_modo_autenticacion_update(cls, v):
        if v is not None:
            modos_validos = ['local', 'sso', 'hybrid']
            if v not in modos_validos:
                raise ValueError(f"modo_autenticacion debe ser uno de: {', '.join(modos_validos)}")
        return v
    
    @validator('plan_suscripcion')
    def validar_plan_suscripcion_update(cls, v):
        if v is not None:
            planes_validos = ['trial', 'basico', 'profesional', 'enterprise']
            if v not in planes_validos:
                raise ValueError(f"plan_suscripcion debe ser uno de: {', '.join(planes_validos)}")
        return v
    
    @validator('estado_suscripcion')
    def validar_estado_suscripcion_update(cls, v):
        if v is not None:
            estados_validos = ['trial', 'activo', 'suspendido', 'cancelado', 'moroso']
            if v not in estados_validos:
                raise ValueError(f"estado_suscripcion debe ser uno de: {', '.join(estados_validos)}")
        return v
    
    @validator('ruc')
    def validar_ruc_update(cls, v):
        if v is not None and v.strip():
            if not v.isdigit():
                raise ValueError("El RUC debe contener solo números")
            if len(v) < 8 or len(v) > 15:
                raise ValueError("El RUC debe tener entre 8 y 15 dígitos")
        return v
    
    @validator('tema_personalizado', 'metadata_json')
    def validar_json_update(cls, v):
        if v is not None and v.strip():
            try:
                json.loads(v)
            except json.JSONDecodeError:
                raise ValueError("Debe ser un JSON válido")
        return v
    
    @validator('servidor_api_local')
    def validar_url_servidor_update(cls, v):
        if v is not None and v.strip():
            if not (v.startswith('http://') or v.startswith('https://')):
                raise ValueError("servidor_api_local debe ser una URL válida (http:// o https://)")
        return v
    
    @validator('fecha_fin_trial')
    def validar_fecha_fin_trial(cls, v, values):
        if v is not None and 'fecha_inicio_suscripcion' in values and values['fecha_inicio_suscripcion'] is not None:
            if v < values['fecha_inicio_suscripcion']:
                raise ValueError("fecha_fin_trial no puede ser anterior a fecha_inicio_suscripcion")
        return v

    class Config:
        from_attributes = True


class ClienteRead(ClienteBase):
    """
    Esquema de lectura completo de un cliente.
    Incluye los campos de auditoría generados por el sistema.
    """
    cliente_id: int = Field(..., description="Identificador único del cliente.")
    fecha_creacion: datetime = Field(..., description="Fecha de creación del registro.")
    fecha_actualizacion: Optional[datetime] = Field(None, description="Fecha de última actualización.")
    fecha_ultimo_acceso: Optional[datetime] = Field(None, description="Última vez que un usuario accedió.")

    class Config:
        from_attributes = True


# Este schema se usará una vez que crees `auth_config.py`
# from app.schemas.auth_config import AuthConfigRead

class ClienteWithConfig(ClienteRead):
    """
    Esquema extendido que incluye la configuración de autenticación del cliente.
    Se usará en endpoints de administración.
    """
    # auth_config: Optional[AuthConfigRead] = Field(None, description="Configuración de autenticación del cliente.")
    # sso_providers: List[SSOProviderRead] = Field(default_factory=list, description="Lista de proveedores SSO activos.")
    pass


class PaginatedClienteResponse(BaseModel):
    """
    Schema para respuestas paginadas de listas de clientes.
    
    Utilizado en endpoints que devuelven listas paginadas de clientes
    con metadatos de paginación.
    """
    clientes: List[ClienteRead] = Field(
        ...,
        description="Lista de clientes para la página actual"
    )
    total_clientes: int = Field(
        ...,
        ge=0,
        description="Número total de clientes que coinciden con los filtros"
    )
    pagina_actual: int = Field(
        ...,
        ge=1,
        description="Número de la página actual siendo visualizada"
    )
    total_paginas: int = Field(
        ...,
        ge=0,
        description="Número total de páginas disponibles"
    )
    items_por_pagina: int = Field(
        ...,
        ge=1,
        description="Número de items por página"
    )

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class ClienteStatsResponse(BaseModel):
    """
    Schema para estadísticas de un cliente.
    """
    cliente_id: int = Field(..., description="ID del cliente")
    razon_social: str = Field(..., description="Razón social del cliente")
    total_usuarios: int = Field(..., ge=0, description="Total de usuarios activos")
    total_usuarios_inactivos: int = Field(..., ge=0, description="Total de usuarios inactivos")
    modulos_activos: int = Field(..., ge=0, description="Número de módulos activos")
    modulos_contratados: int = Field(..., ge=0, description="Número de módulos contratados")
    ultimo_acceso: Optional[datetime] = Field(None, description="Última vez que un usuario accedió")
    estado_suscripcion: str = Field(..., description="Estado actual de la suscripción")
    plan_actual: str = Field(..., description="Plan de suscripción actual")
    fecha_creacion: datetime = Field(..., description="Fecha de creación del cliente")
    dias_activo: int = Field(..., ge=0, description="Días desde la creación")
    conexiones_bd: int = Field(..., ge=0, description="Número de conexiones de BD configuradas")
    tipo_instalacion: str = Field(..., description="Tipo de instalación (cloud/onpremise/hybrid)")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class ClienteResponse(BaseModel):
    """
    Schema estándar para respuestas de operaciones exitosas sobre clientes.
    """
    success: bool = Field(True, description="Indica si la operación fue exitosa")
    message: str = Field(..., description="Mensaje descriptivo de la operación")
    data: Optional[ClienteRead] = Field(None, description="Datos del cliente (si aplica)")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class ClienteDeleteResponse(BaseModel):
    """
    Schema para respuesta de eliminación de cliente.
    """
    success: bool = Field(True, description="Indica si la eliminación fue exitosa")
    message: str = Field(..., description="Mensaje descriptivo")
    cliente_id: int = Field(..., description="ID del cliente eliminado")
    
    class Config:
        from_attributes = True


class BrandingRead(BaseModel):
    """
    Schema de respuesta para configuración de branding del tenant.
    Contiene solo los campos visuales necesarios para el frontend.
    
    Este schema se utiliza en el endpoint GET /api/v1/clientes/tenant/branding
    para exponer la configuración de personalización visual del cliente actual.
    """
    logo_url: Optional[str] = Field(
        None, 
        max_length=500, 
        description="URL pública del logo del cliente"
    )
    favicon_url: Optional[str] = Field(
        None, 
        max_length=500, 
        description="URL del favicon personalizado"
    )
    color_primario: str = Field(
        "#1976D2", 
        description="Color principal en formato HEX (#RRGGBB)"
    )
    color_secundario: str = Field(
        "#424242", 
        description="Color secundario en formato HEX"
    )
    tema_personalizado: Optional[Dict[str, Any]] = Field(
        None, 
        description="Configuración avanzada de tema (JSON parseado como objeto)"
    )
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }