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

# Reutilizar schemas existentes
from .superadmin_usuario import ClienteInfo, UsuarioInfo


class AuthAuditLogRead(BaseModel):
    """
    Vista completa de un log de autenticación.
    """
    log_id: int = Field(..., description="ID único del log")
    cliente_id: int = Field(..., description="ID del cliente")
    cliente: Optional[ClienteInfo] = Field(None, description="Información del cliente")
    usuario_id: Optional[int] = Field(None, description="ID del usuario (NULL si evento anónimo)")
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
    log_id: int = Field(..., description="ID único del log")
    cliente_origen_id: Optional[int] = Field(None, description="ID del cliente origen")
    cliente_origen: Optional[ClienteInfo] = Field(None, description="Información del cliente origen")
    cliente_destino_id: Optional[int] = Field(None, description="ID del cliente destino")
    cliente_destino: Optional[ClienteInfo] = Field(None, description="Información del cliente destino")
    usuario_id: int = Field(..., description="ID del usuario sincronizado")
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
    usuario_ejecutor_id: Optional[int] = Field(None, description="ID del usuario que ejecutó")
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
    usuario_id: int = Field(..., description="ID del usuario")
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

