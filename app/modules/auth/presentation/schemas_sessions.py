"""Schemas IAM-SESSIONS-V1 — sesiones activas (usuario + base compartida)."""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

SessionStatus = Literal["active", "expiring_soon"]


class SessionDeviceRead(BaseModel):
    """Dispositivo enriquecido (derivado en lectura; sin UA crudo)."""

    model_config = ConfigDict(from_attributes=True)

    client_type: str = Field(..., description="Tipo de cliente (web/mobile)")
    browser: str = Field(..., description="Navegador o cliente HTTP")
    browser_version: Optional[str] = Field(None, description="Versión del navegador")
    os: str = Field(..., description="Sistema operativo")
    platform: str = Field(
        ...,
        description="Plataforma derivada: desktop, mobile, tablet, unknown",
    )
    device_label: str = Field(..., description="Etiqueta legible para display")
    ip_address: Optional[str] = Field(None, description="Última IP conocida")
    device_id: Optional[str] = Field(None, description="Identificador de dispositivo (puede ser null)")


class SessionReadBase(BaseModel):
    """Base compartida user/admin — incluye alias legacy para compatibilidad."""

    model_config = ConfigDict(from_attributes=True)

    token_id: UUID = Field(..., description="ID del refresh token vigente (PK)")
    usuario_id: UUID = Field(..., description="Usuario propietario de la sesión")
    cliente_id: UUID = Field(..., description="Tenant de la sesión")
    empresa_id: Optional[UUID] = Field(None, description="Empresa activa de la sesión")
    empresa_nombre: Optional[str] = Field(None, description="Nombre de la empresa activa")

    issued_at: datetime = Field(
        ...,
        description="Emisión del refresh vigente (alias semántico de created_at)",
    )
    created_at: datetime = Field(
        ...,
        description="Legacy — misma fecha que issued_at (emisión refresh vigente)",
    )
    last_refresh_at: Optional[datetime] = Field(
        None,
        description="Última renovación/validación refresh",
    )
    last_used_at: Optional[datetime] = Field(
        None,
        description="Legacy — misma fecha que last_refresh_at",
    )
    expires_at: datetime = Field(..., description="Expiración del refresh token")

    is_current: bool = Field(
        False,
        description="True si coincide con el refresh token del request",
    )
    status: SessionStatus = Field(
        "active",
        description="Estado derivado: active | expiring_soon (<24h)",
    )
    duration_seconds: int = Field(
        ...,
        ge=0,
        description="Segundos desde issued_at hasta ahora",
    )

    device: SessionDeviceRead = Field(..., description="Dispositivo enriquecido")
    client_type: str = Field(..., description="Tipo de cliente (web/mobile)")

    ip_address: Optional[str] = Field(
        None,
        description="Legacy — misma IP que device.ip_address (raíz del DTO)",
    )

    device_name: Optional[str] = Field(None, description="Legacy — columna BD (puede ser null)")
    device_id: Optional[str] = Field(None, description="Legacy — columna BD (puede ser null)")


class UserSessionRead(SessionReadBase):
    """Sesión activa del usuario autenticado."""

    pass
