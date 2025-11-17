"""
Esquemas Pydantic para la entidad AuthConfig en arquitectura multi-tenant.
Estos esquemas definen la estructura de datos para la configuración de políticas
de autenticación y seguridad por cliente, incluyendo políticas de contraseñas,
configuración de 2FA, control de sesiones y restricciones de acceso.

Características clave:
- Configuración granular de políticas de seguridad por cliente
- Validación de coherencia entre políticas relacionadas
- Soporte para 2FA, whitelist/blacklist de IPs, horarios de acceso
- Valores por defecto coherentes con mejores prácticas de seguridad
- Total coherencia con la estructura de la tabla cliente_auth_config
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator, field_validator
import json
import re


class AuthConfigBase(BaseModel):
    """
    Esquema base para la entidad AuthConfig, alineado con la tabla cliente_auth_config.
    Define las políticas de autenticación y seguridad específicas para cada cliente.
    """
    # ========================================
    # POLÍTICAS DE CONTRASEÑA
    # ========================================
    password_min_length: int = Field(
        8, 
        description="Longitud mínima de contraseña."
    )
    password_require_uppercase: bool = Field(
        True, 
        description="Requiere al menos una letra mayúscula."
    )
    password_require_lowercase: bool = Field(
        True, 
        description="Requiere al menos una letra minúscula."
    )
    password_require_number: bool = Field(
        True, 
        description="Requiere al menos un número."
    )
    password_require_special: bool = Field(
        False, 
        description="Requiere al menos un carácter especial (!@#$%^&*)."
    )
    password_expiry_days: int = Field(
        90, 
        description="Días antes de expirar la contraseña (0 = nunca expira)."
    )
    password_history_count: int = Field(
        3, 
        description="Cuántas contraseñas previas recordar (no permitir reutilizar)."
    )

    # ========================================
    # CONTROL DE ACCESO Y SESIONES
    # ========================================
    max_login_attempts: int = Field(
        5, 
        description="Máximo de intentos fallidos antes de bloquear."
    )
    lockout_duration_minutes: int = Field(
        30, 
        description="Duración del bloqueo en minutos."
    )
    max_active_sessions: int = Field(
        3, 
        description="Máximo de sesiones simultáneas por usuario (0 = ilimitado)."
    )
    session_idle_timeout_minutes: int = Field(
        60, 
        description="Minutos de inactividad antes de cerrar sesión (0 = no expira)."
    )

    # ========================================
    # TOKENS JWT
    # ========================================
    access_token_minutes: int = Field(
        15, 
        description="Duración del access token en minutos."
    )
    refresh_token_days: int = Field(
        30, 
        description="Duración del refresh token en días."
    )

    # ========================================
    # OPCIONES DE LOGIN Y RECUPERACIÓN
    # ========================================
    allow_remember_me: bool = Field(
        True, 
        description="Permitir opción 'Recordar sesión'."
    )
    remember_me_days: int = Field(
        30, 
        description="Duración de sesión si marca 'recordar' (en días)."
    )
    require_email_verification: bool = Field(
        False, 
        description="Requiere verificar email antes de primer login."
    )
    allow_password_reset: bool = Field(
        True, 
        description="Permitir recuperación de contraseña por email."
    )

    # ========================================
    # AUTENTICACIÓN DE DOS FACTORES (2FA)
    # ========================================
    enable_2fa: bool = Field(
        False, 
        description="Habilitar 2FA para el cliente."
    )
    require_2fa_for_admins: bool = Field(
        False, 
        description="Forzar 2FA para usuarios con rol admin."
    )
    metodos_2fa_permitidos: str = Field(
        "email,sms", 
        description="Métodos permitidos separados por coma: 'email', 'sms', 'totp', 'app'."
    )

    # ========================================
    # WHITELIST/BLACKLIST DE IPs
    # ========================================
    ip_whitelist_enabled: bool = Field(
        False, 
        description="Habilitar whitelist de IPs permitidas."
    )
    ip_whitelist: Optional[str] = Field(
        None, 
        description="JSON array de IPs permitidas (ej: [\"192.168.1.0/24\", \"10.0.0.1\"])."
    )
    ip_blacklist: Optional[str] = Field(
        None, 
        description="JSON array de IPs bloqueadas."
    )

    # ========================================
    # HORARIOS DE ACCESO
    # ========================================
    horario_acceso_enabled: bool = Field(
        False, 
        description="Habilitar restricción por horarios."
    )
    horario_acceso_config: Optional[str] = Field(
        None, 
        description="JSON con horarios permitidos (ej: {\"lunes\": \"08:00-18:00\"})."
    )

    # === VALIDADORES ===
    @validator('password_min_length')
    def validar_longitud_minima_password(cls, v):
        """
        Valida que la longitud mínima de contraseña sea segura.
        """
        if v < 6:
            raise ValueError("La longitud mínima de contraseña debe ser al menos 6 caracteres.")
        if v > 128:
            raise ValueError("La longitud mínima de contraseña no puede exceder 128 caracteres.")
        return v

    @validator('password_expiry_days')
    def validar_expiracion_password(cls, v):
        """
        Valida que los días de expiración sean razonables.
        """
        if v < 0:
            raise ValueError("Los días de expiración de contraseña no pueden ser negativos.")
        if v > 365:
            raise ValueError("Los días de expiración de contraseña no pueden exceder 1 año.")
        return v

    @validator('max_login_attempts')
    def validar_intentos_login(cls, v):
        """
        Valida que el número máximo de intentos sea razonable.
        """
        if v < 1:
            raise ValueError("El número máximo de intentos de login debe ser al menos 1.")
        if v > 20:
            raise ValueError("El número máximo de intentos de login no puede exceder 20.")
        return v

    @validator('lockout_duration_minutes')
    def validar_duracion_bloqueo(cls, v):
        """
        Valida que la duración del bloqueo sea razonable.
        """
        if v < 1:
            raise ValueError("La duración del bloqueo debe ser al menos 1 minuto.")
        if v > 1440:  # 24 horas
            raise ValueError("La duración del bloqueo no puede exceder 24 horas.")
        return v

    @validator('access_token_minutes')
    def validar_duracion_access_token(cls, v):
        """
        Valida que la duración del access token sea segura.
        """
        if v < 1:
            raise ValueError("La duración del access token debe ser al menos 1 minuto.")
        if v > 1440:  # 24 horas
            raise ValueError("La duración del access token no puede exceder 24 horas.")
        return v

    @validator('refresh_token_days')
    def validar_duracion_refresh_token(cls, v):
        """
        Valida que la duración del refresh token sea razonable.
        """
        if v < 1:
            raise ValueError("La duración del refresh token debe ser al menos 1 día.")
        if v > 365:
            raise ValueError("La duración del refresh token no puede exceder 1 año.")
        return v

    @validator('metodos_2fa_permitidos')
    def validar_metodos_2fa(cls, v):
        """
        Valida que los métodos 2FA sean soportados.
        """
        metodos_validos = ['email', 'sms', 'totp', 'app']
        metodos_provistos = [m.strip().lower() for m in v.split(',')]
        
        for metodo in metodos_provistos:
            if metodo not in metodos_validos:
                raise ValueError(f"Método 2FA no soportado: {metodo}. Use: {', '.join(metodos_validos)}")
        
        return v

    @validator('ip_whitelist', 'ip_blacklist')
    def validar_json_ips(cls, v):
        """
        Valida que las listas de IPs sean JSON válidos.
        """
        if v is not None:
            try:
                ips = json.loads(v)
                if not isinstance(ips, list):
                    raise ValueError("Debe ser un array JSON de IPs.")
                
                # Validar formato básico de cada IP
                for ip in ips:
                    if not isinstance(ip, str) or not ip.strip():
                        raise ValueError("Cada IP debe ser una cadena no vacía.")
            except json.JSONDecodeError as e:
                raise ValueError(f"JSON inválido en lista de IPs: {str(e)}")
        return v

    @validator('horario_acceso_config')
    def validar_horarios_acceso(cls, v):
        """
        Valida que la configuración de horarios sea JSON válido.
        """
        if v is not None:
            try:
                horarios = json.loads(v)
                if not isinstance(horarios, dict):
                    raise ValueError("Debe ser un objeto JSON con días y horarios.")
            except json.JSONDecodeError as e:
                raise ValueError(f"JSON inválido en horarios de acceso: {str(e)}")
        return v

    @field_validator('max_active_sessions')
    @classmethod
    def validar_sesiones_activas(cls, v: int) -> int:
        """
        Valida que el máximo de sesiones activas sea razonable.
        """
        if v < 0:
            raise ValueError("El máximo de sesiones activas no puede ser negativo.")
        if v > 50:
            raise ValueError("El máximo de sesiones activas no puede exceder 50.")
        return v

    class Config:
        from_attributes = True


class AuthConfigCreate(AuthConfigBase):
    """
    Esquema para la creación de una nueva configuración de autenticación.
    Incluye el ID del cliente al que pertenece la configuración.
    """
    cliente_id: int = Field(..., description="ID del cliente dueño de esta configuración.")


class AuthConfigUpdate(BaseModel):
    """
    Esquema para la actualización parcial de una configuración de autenticación.
    Todos los campos son opcionales para permitir actualizaciones incrementales.
    """
    password_min_length: Optional[int] = None
    password_require_uppercase: Optional[bool] = None
    password_require_lowercase: Optional[bool] = None
    password_require_number: Optional[bool] = None
    password_require_special: Optional[bool] = None
    password_expiry_days: Optional[int] = None
    password_history_count: Optional[int] = None
    max_login_attempts: Optional[int] = None
    lockout_duration_minutes: Optional[int] = None
    max_active_sessions: Optional[int] = None
    session_idle_timeout_minutes: Optional[int] = None
    access_token_minutes: Optional[int] = None
    refresh_token_days: Optional[int] = None
    allow_remember_me: Optional[bool] = None
    remember_me_days: Optional[int] = None
    require_email_verification: Optional[bool] = None
    allow_password_reset: Optional[bool] = None
    enable_2fa: Optional[bool] = None
    require_2fa_for_admins: Optional[bool] = None
    metodos_2fa_permitidos: Optional[str] = None
    ip_whitelist_enabled: Optional[bool] = None
    ip_whitelist: Optional[str] = None
    ip_blacklist: Optional[str] = None
    horario_acceso_enabled: Optional[bool] = None
    horario_acceso_config: Optional[str] = None

    class Config:
        from_attributes = True


class AuthConfigRead(AuthConfigBase):
    """
    Esquema de lectura completo de una configuración de autenticación.
    Incluye campos de identificación y auditoría generados por el sistema.
    """
    config_id: int = Field(..., description="Identificador único de la configuración.")
    cliente_id: int = Field(..., description="ID del cliente dueño de esta configuración.")
    fecha_creacion: datetime = Field(..., description="Fecha de creación del registro.")
    fecha_actualizacion: Optional[datetime] = Field(None, description="Fecha de última actualización.")

    class Config:
        from_attributes = True


class AuthConfigConEstadisticas(AuthConfigRead):
    """
    Esquema extendido que incluye estadísticas de seguridad del cliente.
    Útil para dashboards de administración y auditoría de seguridad.
    """
    total_usuarios: int = Field(0, description="Total de usuarios del cliente.")
    usuarios_con_2fa: int = Field(0, description="Usuarios con 2FA habilitado.")
    bloqueos_ultima_semana: int = Field(0, description="Cuentas bloqueadas en la última semana.")
    intentos_fallidos_ultimo_mes: int = Field(0, description="Intentos de login fallidos en el último mes.")
    promedio_sesiones_activas: Optional[float] = Field(
        None, 
        description="Promedio de sesiones activas simultáneas."
    )
    cumplimiento_politicas: Optional[float] = Field(
        None, 
        description="Porcentaje de cumplimiento de políticas de seguridad (0-100)."
    )