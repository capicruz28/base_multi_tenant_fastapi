"""Schemas IAM-SESSIONS-PA-001 — listado admin de sesiones activas."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AdminSessionRead(BaseModel):
    """Sesión activa (refresh token vigente) para administración tenant."""

    token_id: UUID = Field(..., description="ID del refresh token (PK)")
    usuario_id: UUID = Field(..., description="Usuario propietario de la sesión")
    cliente_id: UUID = Field(..., description="Tenant de la sesión")
    created_at: datetime = Field(..., description="Fecha de creación de la sesión")
    last_used_at: Optional[datetime] = Field(None, description="Último uso del refresh token")
    expires_at: datetime = Field(..., description="Expiración del refresh token")
    device_name: Optional[str] = Field(None, description="Nombre del dispositivo")
    device_id: Optional[str] = Field(None, description="Identificador del dispositivo")
    ip_address: Optional[str] = Field(None, description="IP de origen")
    user_agent: Optional[str] = Field(None, description="User-Agent registrado")
    client_type: str = Field(..., description="Tipo de cliente (web/mobile)")
    nombre_usuario: Optional[str] = Field(None, description="Login del usuario")
    nombre: Optional[str] = Field(None, description="Nombre del usuario")
    apellido: Optional[str] = Field(None, description="Apellido del usuario")

    class Config:
        from_attributes = True


class PaginatedAdminSessionsResponse(BaseModel):
    """Envelope paginado para GET /auth/sessions/admin/ (modo page+limit)."""

    sessions: List[AdminSessionRead] = Field(..., description="Página actual de sesiones")
    total_sesiones: int = Field(..., ge=0, description="Total post-filtros")
    pagina_actual: int = Field(..., ge=1, description="Página devuelta")
    total_paginas: int = Field(..., ge=0, description="Total de páginas")
    limit: int = Field(..., ge=1, le=100, description="Tamaño de página efectivo")

    class Config:
        from_attributes = True
