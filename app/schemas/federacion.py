from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

# --- Enumeración de Proveedores SSO ---

class SsoProvider(str, Enum):
    """Proveedores de identidad soportados para la federación."""
    AZURE_AD = "AZURE_AD"
    GOOGLE = "GOOGLE_WORKSPACE"
    OKTA = "OKTA"
    CUSTOM = "CUSTOM_SAML_OIDC"

# --- Sub-Schemas para Configuraciones Específicas SSO ---

class SSOConfigAzure(BaseModel):
    """Configuración específica para Azure Active Directory."""
    tenant_id: str = Field(..., description="ID del Inquilino (Tenant ID) de Azure AD.")
    client_id: str = Field(..., description="ID de la Aplicación (Client ID) registrado en Azure.")
    client_secret: Optional[str] = Field(None, description="Secreto de la Aplicación (Client Secret).")
    scope: str = Field("openid profile email", description="Scopes solicitados (ej: openid profile email).")
    allowed_domains: List[str] = Field([], description="Dominios de correo permitidos para el login.")
    
    class Config:
        from_attributes = True

class SSOConfigGoogle(BaseModel):
    """Configuración específica para Google Workspace/Google Identity Platform."""
    client_id: str = Field(..., description="ID de Cliente de OAuth 2.0 de Google.")
    client_secret: Optional[str] = Field(None, description="Secreto de Cliente de OAuth 2.0.")
    hosted_domain: Optional[str] = Field(None, description="Dominio de Google Workspace para restringir el acceso.")
    allowed_domains: List[str] = Field([], description="Dominios de correo permitidos adicionales.")
    
    class Config:
        from_attributes = True

# --- Esquemas Principales de Federación ---

class FederacionBase(BaseModel):
    """Esquema base para la creación y lectura de una configuración de federación."""
    proveedor: SsoProvider = Field(..., description="Proveedor de identidad.")
    es_activo: bool = Field(True, description="Indica si esta configuración de federación está activa.")
    
    class Config:
        from_attributes = True

class FederacionCreate(FederacionBase):
    """Esquema para crear una nueva configuración de federación."""
    configuracion: dict = Field(..., description="Configuración detallada del proveedor (JSON/dict).")

class FederacionUpdate(FederacionBase):
    """Esquema para actualizar una configuración de federación. Todos los campos son opcionales."""
    proveedor: Optional[SsoProvider] = None
    es_activo: Optional[bool] = None
    configuracion: Optional[dict] = Field(None, description="Configuración detallada (opcional).")

class FederacionRead(FederacionBase):
    """Esquema de lectura para una configuración de federación."""
    federacion_id: int = Field(..., description="ID único de la configuración de federación.")
    cliente_id: int = Field(..., description="ID del cliente al que pertenece esta configuración.")
    configuracion_json: dict = Field(..., alias="configuracion", description="Configuración detallada del proveedor (JSON).") 
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime] = None

    class Config:
        from_attributes = True
        populate_by_name = True