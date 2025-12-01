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
        }# app/schemas/modulo.py
"""
Esquemas Pydantic para la entidad Modulo en arquitectura multi-tenant.
Estos esquemas definen la estructura de datos para el catálogo de módulos del sistema,
incluyendo validación de códigos únicos, configuración de módulos core y opcionales,
y gestión del ciclo de vida de módulos.

Características clave:
- Validación estricta de códigos de módulo únicos
- Soporte para módulos core (esenciales) y módulos con licencia
- Configuración de ordenamiento y visibilidad
- Total coherencia con la estructura de la tabla cliente_modulo
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator, field_validator
import re


class ModuloBase(BaseModel):
    """
    Esquema base para la entidad Modulo, alineado con la tabla cliente_modulo.
    Define el catálogo central de módulos disponibles en el sistema multi-tenant.
    """
    # ========================================
    # IDENTIFICACIÓN Y DESCRIPCIÓN
    # ========================================
    codigo_modulo: str = Field(
        ..., 
        max_length=30, 
        description="Código único para referencia en código (ej: 'PLANILLAS', 'CONTABILIDAD')."
    )
    nombre: str = Field(
        ..., 
        max_length=100, 
        description="Nombre descriptivo del módulo."
    )
    descripcion: Optional[str] = Field(
        None, 
        max_length=255, 
        description="Descripción detallada de la funcionalidad del módulo."
    )
    icono: Optional[str] = Field(
        None, 
        max_length=50, 
        description="Nombre del icono representativo (depende de librería UI usada)."
    )

    # ========================================
    # CONFIGURACIÓN DEL MÓDULO
    # ========================================
    es_modulo_core: bool = Field(
        False, 
        description="True = Módulo esencial del sistema (siempre disponible)."
    )
    requiere_licencia: bool = Field(
        False, 
        description="True = Requiere licencia/pago adicional."
    )
    orden: int = Field(
        0, 
        description="Orden de visualización en UI (menor = primero)."
    )
    es_activo: bool = Field(
        True, 
        description="Indica si el módulo está disponible para activación."
    )

    # === VALIDADORES ===
    @validator('codigo_modulo')
    def validar_codigo_modulo(cls, v):
        """
        Valida que el código de módulo tenga formato válido (solo mayúsculas, números y guiones bajos).
        """
        if not re.match(r"^[A-Z][A-Z0-9_]*$", v):
            raise ValueError(
                "El código de módulo debe contener solo letras mayúsculas, números y guiones bajos, "
                "y debe comenzar con una letra."
            )
        if len(v) < 3 or len(v) > 30:
            raise ValueError("El código de módulo debe tener entre 3 y 30 caracteres.")
        return v

    @validator('orden')
    def validar_orden_positivo(cls, v):
        """
        Valida que el orden sea un número positivo.
        """
        if v < 0:
            raise ValueError("El orden debe ser un número positivo o cero.")
        return v

    @field_validator('nombre')
    @classmethod
    def validar_nombre_no_vacio(cls, v: str) -> str:
        """
        Valida que el nombre no esté vacío.
        """
        if not v or not v.strip():
            raise ValueError("El nombre del módulo no puede estar vacío.")
        return v.strip()

    class Config:
        from_attributes = True


class ModuloCreate(ModuloBase):
    """
    Esquema para la creación de un nuevo módulo en el catálogo del sistema.
    Hereda todos los campos de ModuloBase.
    """
    pass


class ModuloUpdate(BaseModel):
    """
    Esquema para la actualización parcial de un módulo.
    Todos los campos son opcionales para permitir actualizaciones incrementales.
    """
    codigo_modulo: Optional[str] = Field(None, max_length=30)
    nombre: Optional[str] = Field(None, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=255)
    icono: Optional[str] = Field(None, max_length=50)
    es_modulo_core: Optional[bool] = None
    requiere_licencia: Optional[bool] = None
    orden: Optional[int] = None
    es_activo: Optional[bool] = None

    class Config:
        from_attributes = True


class ModuloRead(ModuloBase):
    """
    Esquema de lectura completo de un módulo.
    Incluye los campos de identificación y auditoría generados por el sistema.
    """
    modulo_id: int = Field(..., description="Identificador único del módulo.")
    fecha_creacion: datetime = Field(..., description="Fecha de creación del registro.")

    class Config:
        from_attributes = True


class ModuloConInfoActivacion(ModuloRead):
    """
    Esquema extendido que incluye información de activación para un cliente específico.
    Útil para endpoints de administración que muestran el estado de módulos por cliente.
    """
    activo_en_cliente: bool = Field(..., description="Indica si el módulo está activo para el cliente.")
    cliente_modulo_activo_id: Optional[int] = Field(None, description="ID del registro de activación.")
    fecha_activacion: Optional[datetime] = Field(None, description="Fecha de activación para el cliente.")
    fecha_vencimiento: Optional[datetime] = Field(None, description="Fecha de vencimiento de la licencia (NULL = ilimitado).")
    configuracion_json: Optional[str] = Field(None, description="Configuración específica para el cliente (JSON string).")
    limite_usuarios: Optional[int] = Field(None, description="Límite de usuarios para este módulo.")
    limite_registros: Optional[int] = Field(None, description="Límite de registros para este módulo.")


# ============================================================================
# SCHEMAS DE RESPUESTA ESTÁNDAR
# Estos schemas estandarizan el formato de respuesta de todos los endpoints
# para facilitar el consumo desde el frontend
# ============================================================================

class PaginationMetadata(BaseModel):
    """
    Metadata de paginación para respuestas paginadas.
    Proporciona toda la información necesaria para implementar paginación en el frontend.
    """
    total: int = Field(..., description="Total de registros disponibles.")
    skip: int = Field(..., description="Número de registros saltados.")
    limit: int = Field(..., description="Límite de registros por página.")
    total_pages: int = Field(..., description="Total de páginas disponibles.")
    current_page: int = Field(..., description="Página actual (1-indexed).")
    has_next: bool = Field(..., description="Indica si existe una página siguiente.")
    has_prev: bool = Field(..., description="Indica si existe una página anterior.")

    class Config:
        from_attributes = True


class ModuloResponse(BaseModel):
    """
    Respuesta estándar para operaciones sobre un módulo individual.
    Usado en endpoints de creación, actualización y consulta de un solo módulo.
    """
    success: bool = Field(True, description="Indica si la operación fue exitosa.")
    message: str = Field(..., description="Mensaje descriptivo de la operación.")
    data: Optional[ModuloRead] = Field(None, description="Datos del módulo.")

    class Config:
        from_attributes = True


class ModuloListResponse(BaseModel):
    """
    Respuesta estándar para listas de módulos sin paginación.
    Usado cuando se retorna una lista completa de módulos.
    """
    success: bool = Field(True, description="Indica si la operación fue exitosa.")
    message: str = Field(..., description="Mensaje descriptivo de la operación.")
    data: List[ModuloRead] = Field(default_factory=list, description="Lista de módulos.")

    class Config:
        from_attributes = True


class ModuloConInfoActivacionListResponse(BaseModel):
    """
    Respuesta estándar para listas de módulos con información de activación.
    Usado en endpoints que muestran módulos con su estado de activación por cliente.
    """
    success: bool = Field(True, description="Indica si la operación fue exitosa.")
    message: str = Field(..., description="Mensaje descriptivo de la operación.")
    data: List[ModuloConInfoActivacion] = Field(default_factory=list, description="Lista de módulos con información de activación.")

    class Config:
        from_attributes = True


class PaginatedModuloResponse(BaseModel):
    """
    Respuesta estándar para listas paginadas de módulos.
    Incluye metadata de paginación para facilitar la navegación en el frontend.
    """
    success: bool = Field(True, description="Indica si la operación fue exitosa.")
    message: str = Field(..., description="Mensaje descriptivo de la operación.")
    data: List[ModuloRead] = Field(default_factory=list, description="Lista de módulos de la página actual.")
    pagination: PaginationMetadata = Field(..., description="Metadata de paginación.")

    class Config:
        from_attributes = True


class ModuloDeleteResponse(BaseModel):
    """
    Respuesta estándar para operaciones de eliminación de módulos.
    Confirma la eliminación exitosa del módulo.
    """
    success: bool = Field(True, description="Indica si la operación fue exitosa.")
    message: str = Field(..., description="Mensaje descriptivo de la operación.")
    modulo_id: int = Field(..., description="ID del módulo eliminado.")

    class Config:
        from_attributes = True
# app/schemas/conexion.py
"""
Esquemas Pydantic para la entidad Conexion en arquitectura multi-tenant.
Estos esquemas definen la estructura de datos para la gestión de conexiones de base de datos
por cliente y módulo, incluyendo validación de configuraciones, encriptación de credenciales
y soporte para múltiples motores de base de datos.

Características clave:
- Validación de configuraciones de conexión a BD
- Soporte para múltiples motores (SQL Server, PostgreSQL, MySQL, Oracle)
- Manejo seguro de credenciales con encriptación
- Configuración de connection pooling y timeouts
- Total coherencia con la estructura de la tabla cliente_modulo_conexion
"""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator, field_validator
import re


class ConexionBase(BaseModel):
    """
    Esquema base para la entidad Conexion, alineado con la tabla cliente_modulo_conexion.
    Define la configuración de conexiones de base de datos específicas por cliente y módulo.
    """
    # ========================================
    # IDENTIFICACIÓN Y CONTEXTO
    # ========================================
    cliente_id: int = Field(..., description="ID del cliente al que pertenece la conexión.")
    modulo_id: int = Field(..., description="ID del módulo para el que se configura la conexión.")

    # ========================================
    # CONFIGURACIÓN DE CONEXIÓN
    # ========================================
    servidor: str = Field(
        ..., 
        max_length=255, 
        description="Nombre o IP del servidor de BD (ej: 'localhost', 'sql.azure.com')."
    )
    puerto: int = Field(
        1433, 
        description="Puerto de conexión (1433 para SQL Server, 5432 para PostgreSQL, etc.)."
    )
    nombre_bd: str = Field(
        ..., 
        max_length=100, 
        description="Nombre de la base de datos (ej: 'bdpla_psf_web', 'produccion_2024')."
    )
    tipo_bd: str = Field(
        "sqlserver", 
        description="Tipo de base de datos: 'sqlserver', 'postgresql', 'mysql', 'oracle'."
    )

    # ========================================
    # CONFIGURACIÓN AVANZADA
    # ========================================
    usa_ssl: bool = Field(
        False, 
        description="Indica si la conexión usa SSL/TLS."
    )
    timeout_segundos: int = Field(
        30, 
        description="Timeout de conexión en segundos."
    )
    max_pool_size: int = Field(
        100, 
        description="Tamaño máximo del connection pool."
    )
    es_solo_lectura: bool = Field(
        False, 
        description="True = Conexión read-only (útil para réplicas)."
    )
    es_conexion_principal: bool = Field(
        False, 
        description="True = Es la conexión principal del módulo (solo una por cliente-módulo)."
    )

    # === VALIDADORES ===
    @validator('servidor')
    def validar_servidor(cls, v):
        """
        Valida el formato del servidor (hostname o IP válida).
        """
        if not v or not v.strip():
            raise ValueError("El servidor no puede estar vacío.")
        
        # Validar como hostname
        if re.match(r"^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?)*$", v):
            return v
            
        # Validar como IPv4
        if re.match(r"^(\d{1,3}\.){3}\d{1,3}$", v):
            octetos = v.split('.')
            if all(0 <= int(octeto) <= 255 for octeto in octetos):
                return v
                
        # Validar como IPv6 (simplificado)
        if ':' in v and re.match(r"^[0-9a-fA-F:]+$", v):
            return v
            
        raise ValueError("Formato de servidor inválido. Use hostname, IPv4 o IPv6 válido.")

    @validator('puerto')
    def validar_puerto(cls, v):
        """
        Valida que el puerto esté en el rango válido.
        """
        if v < 1 or v > 65535:
            raise ValueError("El puerto debe estar entre 1 y 65535.")
        return v

    @validator('tipo_bd')
    def validar_tipo_bd(cls, v):
        """
        Valida que el tipo de base de datos sea soportado.
        """
        tipos_validos = ['sqlserver', 'postgresql', 'mysql', 'oracle']
        if v not in tipos_validos:
            raise ValueError(f"Tipo de BD no soportado. Use: {', '.join(tipos_validos)}")
        return v

    @validator('timeout_segundos')
    def validar_timeout(cls, v):
        """
        Valida que el timeout sea razonable.
        """
        if v < 5 or v > 300:
            raise ValueError("El timeout debe estar entre 5 y 300 segundos.")
        return v

    @validator('max_pool_size')
    def validar_pool_size(cls, v):
        """
        Valida que el tamaño del pool sea razonable.
        """
        if v < 1 or v > 1000:
            raise ValueError("El tamaño máximo del pool debe estar entre 1 y 1000.")
        return v

    @field_validator('nombre_bd')
    @classmethod
    def validar_nombre_bd(cls, v: str) -> str:
        """
        Valida que el nombre de BD no esté vacío y tenga formato válido.
        """
        if not v or not v.strip():
            raise ValueError("El nombre de la base de datos no puede estar vacío.")
        
        # Validar caracteres básicos para nombres de BD
        if not re.match(r"^[a-zA-Z0-9_][a-zA-Z0-9_\-\.]*$", v):
            raise ValueError(
                "El nombre de la base de datos solo puede contener letras, números, "
                "guiones bajos, guiones y puntos, y debe comenzar con letra o número."
            )
        return v.strip()

    class Config:
        from_attributes = True


class ConexionCreate(ConexionBase):
    """
    Esquema para la creación de una nueva conexión de base de datos.
    Incluye campos para credenciales en texto plano que serán encriptadas.
    """
    usuario: str = Field(..., description="Usuario de BD para encriptar.")
    password: str = Field(..., description="Password de BD para encriptar.")


class ConexionUpdate(BaseModel):
    """
    Esquema para la actualización parcial de una conexión.
    Todos los campos son opcionales, incluyendo credenciales.
    """
    servidor: Optional[str] = Field(None, max_length=255)
    puerto: Optional[int] = None
    nombre_bd: Optional[str] = Field(None, max_length=100)
    usuario: Optional[str] = Field(None, description="Nuevo usuario de BD (se encriptará).")
    password: Optional[str] = Field(None, description="Nuevo password de BD (se encriptará).")
    tipo_bd: Optional[str] = None
    usa_ssl: Optional[bool] = None
    timeout_segundos: Optional[int] = None
    max_pool_size: Optional[int] = None
    es_solo_lectura: Optional[bool] = None
    es_conexion_principal: Optional[bool] = None
    es_activo: Optional[bool] = None

    class Config:
        from_attributes = True


class ConexionRead(ConexionBase):
    """
    Esquema de lectura completo de una conexión.
    Incluye campos de identificación, auditoría y estado de la conexión.
    Los campos de credenciales muestran versiones encriptadas.
    """
    conexion_id: int = Field(..., description="Identificador único de la conexión.")
    usuario_encriptado: str = Field(..., description="Usuario de BD encriptado.")
    password_encriptado: str = Field(..., description="Password de BD encriptado.")
    connection_string_encriptado: Optional[str] = Field(
        None, 
        description="Connection string completo encriptado."
    )
    es_activo: bool = Field(..., description="Indica si la conexión está activa.")
    ultima_conexion_exitosa: Optional[datetime] = Field(
        None, 
        description="Última vez que se conectó exitosamente."
    )
    ultimo_error: Optional[str] = Field(None, description="Último mensaje de error de conexión.")
    fecha_ultimo_error: Optional[datetime] = Field(None, description="Fecha del último error.")
    fecha_creacion: datetime = Field(..., description="Fecha de creación del registro.")
    fecha_actualizacion: Optional[datetime] = Field(None, description="Fecha de última actualización.")
    creado_por_usuario_id: Optional[int] = Field(None, description="ID del usuario que creó la conexión.")

    class Config:
        from_attributes = True


class ConexionTest(BaseModel):
    """
    Esquema para testing de conectividad de una configuración de conexión.
    Permite probar conexiones sin guardarlas en la base de datos.
    """
    servidor: str = Field(..., max_length=255)
    puerto: int = Field(1433)
    nombre_bd: str = Field(..., max_length=100)
    usuario: str = Field(..., description="Usuario de BD para testing.")
    password: str = Field(..., description="Password de BD para testing.")
    tipo_bd: str = Field("sqlserver")
    usa_ssl: bool = Field(False)
    timeout_segundos: int = Field(30)

    class Config:
        from_attributes = True


class ConexionConEstadisticas(ConexionRead):
    """
    Esquema extendido que incluye estadísticas de uso de la conexión.
    Útil para monitoreo y troubleshooting.
    """
    total_conexiones: int = Field(0, description="Total de conexiones establecidas.")
    conexiones_activas: int = Field(0, description="Conexiones activas actualmente.")
    tiempo_promedio_respuesta: Optional[float] = Field(
        None, 
        description="Tiempo promedio de respuesta en milisegundos."
    )
    tasa_errores: Optional[float] = Field(
        None, 
        description="Porcentaje de errores en las últimas conexiones."
    )


# ============================================================================
# SCHEMAS DE MÓDULO ACTIVO
# Esquemas Pydantic para la entidad ModuloActivo en arquitectura multi-tenant.
# Estos esquemas definen la estructura de datos para la activación y configuración
# de módulos específicos por cliente, incluyendo límites de uso, configuraciones
# personalizadas y gestión del ciclo de vida de licencias.
# ============================================================================

class ModuloActivoBase(BaseModel):
    """
    Esquema base para la entidad ModuloActivo, alineado con la tabla cliente_modulo_activo.
    Define la relación entre clientes y módulos activados con sus configuraciones específicas.
    """
    # ========================================
    # IDENTIFICACIÓN Y CONTEXTO
    # ========================================
    cliente_id: int = Field(..., description="ID del cliente que activa el módulo.")
    modulo_id: int = Field(..., description="ID del módulo que se activa.")

    # ========================================
    # CONFIGURACIÓN Y LÍMITES
    # ========================================
    configuracion_json: Optional[Dict[str, Any]] = Field(
        None, 
        description="JSON con configuraciones custom del módulo para este cliente."
    )
    limite_usuarios: Optional[int] = Field(
        None, 
        description="Máximo de usuarios que pueden usar este módulo (NULL = ilimitado)."
    )
    limite_registros: Optional[int] = Field(
        None, 
        description="Límite de registros para este módulo (NULL = ilimitado)."
    )
    fecha_vencimiento: Optional[datetime] = Field(
        None,
        description="Fecha de vencimiento de la licencia (NULL = ilimitado/permanente)."
    )

    # === VALIDADORES ===
    @validator('limite_usuarios')
    def validar_limite_usuarios(cls, v):
        """
        Valida que el límite de usuarios sea positivo si se especifica.
        """
        if v is not None and v < 1:
            raise ValueError("El límite de usuarios debe ser al menos 1 o NULL para ilimitado.")
        return v

    @validator('limite_registros')
    def validar_limite_registros(cls, v):
        """
        Valida que el límite de registros sea positivo si se especifica.
        """
        if v is not None and v < 0:
            raise ValueError("El límite de registros debe ser al menos 0 o NULL para ilimitado.")
        return v

    @validator('configuracion_json')
    def validar_configuracion_json(cls, v):
        """
        Valida que la configuración JSON sea un objeto válido.
        """
        if v is not None:
            try:
                # Verificar que se puede serializar a JSON
                import json
                json.dumps(v)
            except (TypeError, ValueError) as e:
                raise ValueError(f"Configuración JSON inválida: {str(e)}")
        return v

    @field_validator('cliente_id', 'modulo_id')
    @classmethod
    def validar_ids_positivos(cls, v: int) -> int:
        """
        Valida que los IDs sean números positivos.
        """
        if v <= 0:
            raise ValueError("Los IDs deben ser números positivos.")
        return v

    class Config:
        from_attributes = True


class ModuloActivoCreate(ModuloActivoBase):
    """
    Esquema para la activación de un módulo para un cliente.
    Hereda todos los campos de ModuloActivoBase.
    """
    
    @validator('fecha_vencimiento')
    def validar_fecha_vencimiento(cls, v):
        """
        Valida que la fecha de vencimiento sea futura si se proporciona.
        Esta validación solo aplica al CREAR/ACTIVAR un módulo.
        Al LEER un módulo, puede tener fecha pasada (módulo vencido).
        """
        if v is not None:
            from datetime import datetime
            if v <= datetime.now():
                raise ValueError("La fecha de vencimiento debe ser futura.")
        return v


class ModuloActivoUpdate(BaseModel):
    """
    Esquema para la actualización parcial de un módulo activo.
    Permite modificar configuraciones y límites sin cambiar el estado de activación.
    """
    configuracion_json: Optional[Dict[str, Any]] = None
    limite_usuarios: Optional[int] = None
    limite_registros: Optional[int] = None
    fecha_vencimiento: Optional[datetime] = Field(
        None, 
        description="Nueva fecha de vencimiento de la licencia."
    )
    esta_activo: Optional[bool] = Field(
        None, 
        description="Cambiar estado de activación del módulo."
    )

    class Config:
        from_attributes = True


class ModuloActivoRead(ModuloActivoBase):
    """
    Esquema de lectura completo de un módulo activo.
    Incluye campos de estado, fechas y relación con la información del módulo.
    """
    cliente_modulo_activo_id: int = Field(..., description="Identificador único del registro de activación.")
    esta_activo: bool = Field(..., description="Indica si el módulo está activo para el cliente.")
    fecha_activacion: datetime = Field(..., description="Fecha de activación del módulo.")
    fecha_vencimiento: Optional[datetime] = Field(
        None, 
        description="Fecha de vencimiento de la licencia (NULL = ilimitado)."
    )
    
    # Información del módulo (join desde cliente_modulo)
    modulo_nombre: Optional[str] = Field(None, description="Nombre del módulo.")
    codigo_modulo: Optional[str] = Field(None, description="Código único del módulo.")
    modulo_descripcion: Optional[str] = Field(None, description="Descripción del módulo.")

    class Config:
        from_attributes = True


class ModuloActivoConEstadisticas(ModuloActivoRead):
    """
    Esquema extendido que incluye estadísticas de uso del módulo activo.
    Útil para dashboards de administración y control de límites.
    """
    usuarios_activos: int = Field(0, description="Número de usuarios activos usando el módulo.")
    registros_totales: int = Field(0, description="Total de registros en el módulo.")
    porcentaje_uso_usuarios: Optional[float] = Field(
        None, 
        description="Porcentaje de uso del límite de usuarios (0-100)."
    )
    porcentaje_uso_registros: Optional[float] = Field(
        None, 
        description="Porcentaje de uso del límite de registros (0-100)."
    )
    dias_restantes_licencia: Optional[int] = Field(
        None, 
        description="Días restantes hasta el vencimiento (NULL = ilimitado)."
    )
    esta_proximo_vencimiento: bool = Field(
        False, 
        description="True si la licencia vence en menos de 30 días."
    )
    esta_sobre_limite: bool = Field(
        False, 
        description="True si se ha excedido algún límite configurado."
    )
