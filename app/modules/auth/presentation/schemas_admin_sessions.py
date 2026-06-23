"""Schemas IAM-SESSIONS-PA-001 + V1 — listado admin de sesiones activas."""
from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field

from app.modules.auth.presentation.schemas_sessions import SessionReadBase


class AdminSessionRead(SessionReadBase):
    """Sesión activa (refresh token vigente) para administración tenant."""

    nombre_usuario: str | None = Field(None, description="Login del usuario")
    nombre: str | None = Field(None, description="Nombre del usuario")
    apellido: str | None = Field(None, description="Apellido del usuario")
    user_agent: str | None = Field(
        None,
        description="User-Agent crudo (solo admin, diagnóstico)",
    )

    class Config:
        from_attributes = True


class PaginatedAdminSessionsResponse(BaseModel):
    """Envelope paginado — dual ERP estándar + legacy (compat FE)."""

    items: List[AdminSessionRead] = Field(..., description="Página actual (ERP estándar)")
    total: int = Field(..., ge=0, description="Total post-filtros (ERP estándar)")
    sessions: List[AdminSessionRead] = Field(..., description="Legacy — misma página que items")
    total_sesiones: int = Field(..., ge=0, description="Legacy — mismo valor que total")
    pagina_actual: int = Field(..., ge=1, description="Página devuelta")
    total_paginas: int = Field(..., ge=0, description="Total de páginas")
    limit: int = Field(..., ge=1, le=100, description="Tamaño de página efectivo")

    class Config:
        from_attributes = True
