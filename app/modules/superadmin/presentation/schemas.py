# app/schemas/superadmin_usuario.py
"""
Esquemas Pydantic exclusivos para Superadmin - Gestión de Usuarios.

Este módulo define schemas específicos para la vista de Superadmin sobre usuarios,
incluyendo información del cliente y capacidades de filtrado global.

Características principales:
- NO modifica schemas existentes en usuario.py
- Incluye información del cliente en respuestas
- Compatible con filtrado por cliente_id opcional
- Reutiliza schemas existentes cuando es posible
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

# Reutilizar schemas existentes
from app.modules.rbac.presentation.schemas import RolRead
from app.modules.tenant.presentation.schemas import ClienteRead


class ClienteInfo(BaseModel):
    """
    Información básica del cliente para incluir en respuestas de usuarios.
    Versión ligera de ClienteRead para evitar sobrecargar respuestas.
    """
    cliente_id: UUID = Field(..., description="ID único del cliente (UUID)")
    razon_social: str = Field(..., description="Razón social del cliente")
    subdominio: str = Field(..., description="Subdominio único del cliente")
    codigo_cliente: Optional[str] = Field(None, description="Código del cliente")
    nombre_comercial: Optional[str] = Field(None, description="Nombre comercial")
    tipo_instalacion: str = Field(default="cloud", description="Tipo de instalación")
    estado_suscripcion: str = Field(default="activo", description="Estado de suscripción")

    class Config:
        from_attributes = True


class UsuarioInfo(BaseModel):
    """
    Información mínima del usuario para incluir en logs y respuestas.
    Versión ligera para evitar sobrecargar respuestas de auditoría.
    """
    usuario_id: UUID = Field(..., description="ID del usuario (UUID)")
    nombre_usuario: str = Field(..., description="Nombre de usuario")
    correo: Optional[str] = Field(None, description="Email del usuario")

    class Config:
        from_attributes = True


class RolInfo(BaseModel):
    """
    Información básica del rol para incluir en respuestas de usuarios.
    Versión ligera de RolRead para evitar sobrecargar respuestas.
    """
    rol_id: UUID = Field(..., description="ID único del rol (UUID)")
    nombre: str = Field(..., description="Nombre del rol")
    codigo_rol: Optional[str] = Field(None, description="Código del rol (si es rol del sistema)")
    nivel_acceso: int = Field(default=1, ge=1, le=5, description="Nivel de acceso del rol")
    es_rol_sistema: bool = Field(default=False, description="Si es rol del sistema")
    fecha_asignacion: Optional[datetime] = Field(None, description="Fecha de asignación del rol")
    es_activo: bool = Field(default=True, description="Si la asignación está activa")

    class Config:
        from_attributes = True


class UsuarioSuperadminRead(BaseModel):
    """
    Vista completa de usuario para Superadmin.
    Incluye información del cliente y todos los datos relevantes.
    """
    usuario_id: UUID = Field(..., description="ID único del usuario (UUID)")
    cliente_id: UUID = Field(..., description="ID del cliente al que pertenece (UUID)")
    cliente: ClienteInfo = Field(..., description="Información del cliente")
    nombre_usuario: str = Field(..., description="Nombre de usuario")
    correo: Optional[str] = Field(None, description="Email del usuario")
    nombre: Optional[str] = Field(None, description="Nombre real")
    apellido: Optional[str] = Field(None, description="Apellido real")
    dni: Optional[str] = Field(None, description="DNI del usuario")
    telefono: Optional[str] = Field(None, description="Teléfono")
    es_activo: bool = Field(..., description="Estado activo/inactivo")
    es_eliminado: bool = Field(default=False, description="Si está eliminado lógicamente")
    proveedor_autenticacion: str = Field(default="local", description="Método de autenticación")
    referencia_externa_id: Optional[str] = Field(None, description="ID en proveedor externo")
    referencia_externa_email: Optional[str] = Field(None, description="Email en proveedor externo")
    correo_confirmado: bool = Field(default=False, description="Si el email está confirmado")
    intentos_fallidos: int = Field(default=0, description="Intentos fallidos de login")
    fecha_bloqueo: Optional[datetime] = Field(None, description="Fecha de bloqueo")
    ultimo_ip: Optional[str] = Field(None, description="IP del último acceso")
    fecha_creacion: datetime = Field(..., description="Fecha de creación")
    fecha_ultimo_acceso: Optional[datetime] = Field(None, description="Último acceso")
    fecha_actualizacion: Optional[datetime] = Field(None, description="Última actualización")
    sincronizado_desde: Optional[str] = Field(None, description="Origen de sincronización")
    fecha_ultima_sincronizacion: Optional[datetime] = Field(None, description="Última sincronización")
    roles: List[RolInfo] = Field(default_factory=list, description="Roles activos del usuario")
    access_level: int = Field(default=1, ge=1, le=5, description="Nivel de acceso máximo")
    is_super_admin: bool = Field(default=False, description="Si es super administrador")
    user_type: str = Field(default="user", description="Tipo de usuario")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class PaginatedUsuarioSuperadminResponse(BaseModel):
    """
    Respuesta paginada de listado global de usuarios para Superadmin.
    """
    usuarios: List[UsuarioSuperadminRead] = Field(..., description="Lista de usuarios")
    total_usuarios: int = Field(..., ge=0, description="Total de usuarios que coinciden")
    pagina_actual: int = Field(..., ge=1, description="Página actual")
    total_paginas: int = Field(..., ge=0, description="Total de páginas")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class UsuarioActividadResponse(BaseModel):
    """
    Actividad reciente de un usuario.
    Combina datos de usuario con eventos de auditoría.
    """
    usuario_id: UUID = Field(..., description="ID del usuario (UUID)")
    ultimo_acceso: Optional[datetime] = Field(None, description="Último acceso del usuario")
    ultimo_ip: Optional[str] = Field(None, description="IP del último acceso")
    total_eventos: int = Field(..., ge=0, description="Total de eventos encontrados")
    eventos: List[dict] = Field(default_factory=list, description="Eventos recientes")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class RefreshTokenInfo(BaseModel):
    """
    Información de un token refresh (sesión).
    NO incluye token_hash por seguridad.
    """
    token_id: UUID = Field(..., description="ID del token (UUID)")
    client_type: str = Field(..., description="Tipo de cliente (web/mobile/desktop)")
    device_name: Optional[str] = Field(None, description="Nombre del dispositivo")
    device_id: Optional[str] = Field(None, description="ID del dispositivo")
    ip_address: Optional[str] = Field(None, description="IP de creación")
    user_agent: Optional[str] = Field(None, description="User agent")
    created_at: datetime = Field(..., description="Fecha de creación")
    expires_at: datetime = Field(..., description="Fecha de expiración")
    is_revoked: bool = Field(..., description="Si fue revocado")
    last_used_at: Optional[datetime] = Field(None, description="Última vez usado")
    uso_count: int = Field(default=0, description="Cuántas veces se usó")
    revoked_at: Optional[datetime] = Field(None, description="Fecha de revocación")
    revoked_reason: Optional[str] = Field(None, description="Motivo de revocación")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class UsuarioSesionesResponse(BaseModel):
    """
    Sesiones activas de un usuario.
    """
    usuario_id: UUID = Field(..., description="ID del usuario (UUID)")
    total_sesiones: int = Field(..., ge=0, description="Total de sesiones")
    sesiones_activas: int = Field(..., ge=0, description="Sesiones activas")
    sesiones: List[RefreshTokenInfo] = Field(default_factory=list, description="Lista de sesiones")

    class Config:
        from_attributes = True

# app/schemas/superadmin_auditoria.py
"""
Esquemas Pydantic exclusivos para Superadmin - Auditoría.

Este módulo define schemas específicos para la vista de Superadmin sobre auditoría,
incluyendo logs de autenticación y sincronización.

Características principales:
- NO modifica schemas existentes
- Incluye información de usuario y cliente en respuestas
- Compatible con filtrado por cliente_id opcional
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# Nota: ClienteInfo y UsuarioInfo ya están definidas arriba en este mismo archivo


class AuthAuditLogRead(BaseModel):
    """
    Vista completa de un log de autenticación.
    """
    log_id: UUID = Field(..., description="ID único del log (UUID)")
    cliente_id: UUID = Field(..., description="ID del cliente (UUID)")
    cliente: Optional[ClienteInfo] = Field(None, description="Información del cliente")
    usuario_id: Optional[UUID] = Field(None, description="ID del usuario (NULL si evento anónimo) (UUID)")
    usuario: Optional[UsuarioInfo] = Field(None, description="Información del usuario")
    evento: str = Field(..., description="Tipo de evento")
    nombre_usuario_intento: Optional[str] = Field(None, description="Usuario intentado (login fallido)")
    descripcion: Optional[str] = Field(None, description="Descripción del evento")
    exito: bool = Field(..., description="Si el evento fue exitoso")
    codigo_error: Optional[str] = Field(None, description="Código de error si aplica")
    ip_address: Optional[str] = Field(None, description="IP del evento")
    user_agent: Optional[str] = Field(None, description="User agent")
    device_info: Optional[str] = Field(None, description="Información del dispositivo")
    geolocation: Optional[str] = Field(None, description="Geolocalización")
    metadata_json: Optional[Dict[str, Any]] = Field(None, description="Metadata adicional (JSON parseado)")
    fecha_evento: datetime = Field(..., description="Fecha y hora del evento")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class PaginatedAuthAuditLogResponse(BaseModel):
    """
    Respuesta paginada de logs de autenticación.
    """
    logs: List[AuthAuditLogRead] = Field(..., description="Lista de logs")
    total_logs: int = Field(..., ge=0, description="Total de logs que coinciden")
    pagina_actual: int = Field(..., ge=1, description="Página actual")
    total_paginas: int = Field(..., ge=0, description="Total de páginas")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class LogSincronizacionRead(BaseModel):
    """
    Vista completa de un log de sincronización.
    """
    log_id: UUID = Field(..., description="ID único del log (UUID)")
    cliente_origen_id: Optional[UUID] = Field(None, description="ID del cliente origen (UUID)")
    cliente_origen: Optional[ClienteInfo] = Field(None, description="Información del cliente origen")
    cliente_destino_id: Optional[UUID] = Field(None, description="ID del cliente destino (UUID)")
    cliente_destino: Optional[ClienteInfo] = Field(None, description="Información del cliente destino")
    usuario_id: UUID = Field(..., description="ID del usuario sincronizado (UUID)")
    usuario: Optional[UsuarioInfo] = Field(None, description="Información del usuario")
    tipo_sincronizacion: str = Field(..., description="Tipo de sincronización")
    direccion: str = Field(..., description="Dirección (push/pull/bidireccional)")
    operacion: str = Field(..., description="Operación (create/update/delete)")
    estado: str = Field(..., description="Estado (exitoso/fallido/parcial/pendiente)")
    mensaje_error: Optional[str] = Field(None, description="Mensaje de error si falló")
    campos_sincronizados: Optional[List[str]] = Field(None, description="Campos sincronizados (JSON parseado)")
    cambios_detectados: Optional[Dict[str, Any]] = Field(None, description="Cambios detectados (JSON parseado)")
    hash_antes: Optional[str] = Field(None, description="Hash antes de sincronización")
    hash_despues: Optional[str] = Field(None, description="Hash después de sincronización")
    fecha_sincronizacion: datetime = Field(..., description="Fecha de sincronización")
    usuario_ejecutor_id: Optional[UUID] = Field(None, description="ID del usuario que ejecutó (UUID)")
    usuario_ejecutor: Optional[UsuarioInfo] = Field(None, description="Información del usuario ejecutor")
    duracion_ms: Optional[int] = Field(None, description="Duración en milisegundos")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class PaginatedLogSincronizacionResponse(BaseModel):
    """
    Respuesta paginada de logs de sincronización.
    """
    logs: List[LogSincronizacionRead] = Field(..., description="Lista de logs")
    total_logs: int = Field(..., ge=0, description="Total de logs que coinciden")
    pagina_actual: int = Field(..., ge=1, description="Página actual")
    total_paginas: int = Field(..., ge=0, description="Total de páginas")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class PeriodoInfo(BaseModel):
    """
    Período de tiempo para estadísticas.
    """
    fecha_desde: datetime = Field(..., description="Fecha inicial")
    fecha_hasta: datetime = Field(..., description="Fecha final")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class AutenticacionStats(BaseModel):
    """
    Estadísticas de autenticación.
    """
    total_eventos: int = Field(..., ge=0, description="Total de eventos")
    login_exitosos: int = Field(..., ge=0, description="Logins exitosos")
    login_fallidos: int = Field(..., ge=0, description="Logins fallidos")
    eventos_por_tipo: Dict[str, int] = Field(default_factory=dict, description="Eventos por tipo")

    class Config:
        from_attributes = True


class SincronizacionStats(BaseModel):
    """
    Estadísticas de sincronización.
    """
    total_sincronizaciones: int = Field(..., ge=0, description="Total de sincronizaciones")
    exitosas: int = Field(..., ge=0, description="Sincronizaciones exitosas")
    fallidas: int = Field(..., ge=0, description="Sincronizaciones fallidas")
    por_tipo: Dict[str, int] = Field(default_factory=dict, description="Sincronizaciones por tipo")

    class Config:
        from_attributes = True


class IPStats(BaseModel):
    """
    Estadísticas por IP.
    """
    ip_address: str = Field(..., description="Dirección IP")
    total_eventos: int = Field(..., ge=0, description="Total de eventos")
    eventos_fallidos: int = Field(..., ge=0, description="Eventos fallidos")

    class Config:
        from_attributes = True


class UsuarioStats(BaseModel):
    """
    Estadísticas por usuario.
    """
    usuario_id: UUID = Field(..., description="ID del usuario (UUID)")
    nombre_usuario: str = Field(..., description="Nombre de usuario")
    total_eventos: int = Field(..., ge=0, description="Total de eventos")

    class Config:
        from_attributes = True


class AuditoriaEstadisticasResponse(BaseModel):
    """
    Estadísticas agregadas de auditoría.
    """
    periodo: PeriodoInfo = Field(..., description="Período de tiempo")
    autenticacion: AutenticacionStats = Field(..., description="Estadísticas de autenticación")
    sincronizacion: SincronizacionStats = Field(..., description="Estadísticas de sincronización")
    top_ips: Optional[List[IPStats]] = Field(None, description="Top IPs con más eventos")
    top_usuarios: Optional[List[UsuarioStats]] = Field(None, description="Top usuarios con más eventos")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

