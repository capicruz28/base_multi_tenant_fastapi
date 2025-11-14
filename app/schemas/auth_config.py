from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

# --- Sub-Schemas para Políticas de Contraseña ---

class PasswordPolicyConfig(BaseModel):
    """Esquema para la configuración detallada de la política de contraseñas."""
    min_length: int = Field(8, description="Longitud mínima requerida.")
    require_uppercase: bool = Field(True, description="Requiere mayúsculas.")
    require_lowercase: bool = Field(True, description="Requiere minúsculas.")
    require_number: bool = Field(True, description="Requiere números.")
    require_special_char: bool = Field(False, description="Requiere caracteres especiales.")
    history_count: int = Field(5, description="Número de contraseñas anteriores a recordar (evitar reutilización).")
    expiration_days: Optional[int] = Field(90, description="Días antes de que expire la contraseña (NULL para nunca).")
    
    class Config:
        from_attributes = True

# --- Esquemas Principales de Configuración de Autenticación ---

class AuthConfigBase(BaseModel):
    """Esquema base para la configuración de autenticación de un cliente."""
    sso_habilitado: bool = Field(False, description="Indica si el Single Sign-On está habilitado para este cliente.")
    autenticacion_dos_factores_habilitada: bool = Field(False, description="Indica si la Autenticación de Dos Factores (2FA) está habilitada por defecto.")
    password_policy: PasswordPolicyConfig = Field(PasswordPolicyConfig(), description="Configuración de la política de contraseñas.")
    
    # Políticas de sesión y bloqueo
    max_session_duration_minutes: int = Field(1440, description="Duración máxima de la sesión en minutos (por defecto 24 horas).")
    max_login_attempts: int = Field(5, description="Máximo de intentos fallidos antes de bloquear la cuenta.")
    lockout_duration_minutes: int = Field(30, description="Duración del bloqueo de la cuenta en minutos.")
    
    class Config:
        from_attributes = True

class AuthConfigUpdate(AuthConfigBase):
    """Esquema para actualizar la configuración de autenticación de un cliente. Todos los campos son opcionales."""
    sso_habilitado: Optional[bool] = None
    autenticacion_dos_factores_habilitada: Optional[bool] = None
    password_policy: Optional[PasswordPolicyConfig] = None
    max_session_duration_minutes: Optional[int] = None
    max_login_attempts: Optional[int] = None
    lockout_duration_minutes: Optional[int] = None

class AuthConfigRead(AuthConfigBase):
    """Esquema de lectura para la configuración de autenticación de un cliente."""
    cliente_id: int = Field(..., description="ID del cliente al que pertenece esta configuración.")
    fecha_actualizacion: Optional[datetime] = None