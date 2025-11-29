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

# Reutilizar schemas existentes
from .rol import RolRead
from .cliente import ClienteRead


class ClienteInfo(BaseModel):
    """
    Información básica del cliente para incluir en respuestas de usuarios.
    Versión ligera de ClienteRead para evitar sobrecargar respuestas.
    """
    cliente_id: int = Field(..., description="ID único del cliente")
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
    usuario_id: int = Field(..., description="ID del usuario")
    nombre_usuario: str = Field(..., description="Nombre de usuario")
    correo: Optional[str] = Field(None, description="Email del usuario")

    class Config:
        from_attributes = True


class RolInfo(BaseModel):
    """
    Información básica del rol para incluir en respuestas de usuarios.
    Versión ligera de RolRead para evitar sobrecargar respuestas.
    """
    rol_id: int = Field(..., description="ID único del rol")
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
    usuario_id: int = Field(..., description="ID único del usuario")
    cliente_id: int = Field(..., description="ID del cliente al que pertenece")
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
    usuario_id: int = Field(..., description="ID del usuario")
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
    token_id: int = Field(..., description="ID del token")
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
    usuario_id: int = Field(..., description="ID del usuario")
    total_sesiones: int = Field(..., ge=0, description="Total de sesiones")
    sesiones_activas: int = Field(..., ge=0, description="Sesiones activas")
    sesiones: List[RefreshTokenInfo] = Field(default_factory=list, description="Lista de sesiones")

    class Config:
        from_attributes = True

