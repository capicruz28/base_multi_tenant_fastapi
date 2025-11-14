from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, validator, field_validator
import re

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
        max_length=15, 
        description="RUC u otro ID fiscal del cliente."
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
    fecha_inicio_suscripcion: Optional[datetime] = Field(
        None, 
        description="Fecha de inicio de la suscripción pagada."
    )
    fecha_fin_trial: Optional[datetime] = Field(
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
    fecha_inicio_suscripcion: Optional[datetime] = None
    fecha_fin_trial: Optional[datetime] = None
    contacto_nombre: Optional[str] = Field(None, max_length=100)
    contacto_email: Optional[EmailStr] = None
    contacto_telefono: Optional[str] = Field(None, max_length=20)
    es_activo: Optional[bool] = None
    es_demo: Optional[bool] = None
    metadata_json: Optional[str] = None

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