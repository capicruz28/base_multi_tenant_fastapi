"""Schemas Pydantic del módulo CFG (Administrador del Motor de Códigos).

Contrato oficial: cfg-implementation-spec/02_API_SPEC.md v1.0 (Etapa 3).
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.shared.pagination.schemas import ErpPaginatedResponse
from app.shared.validators import normalize_strip, normalize_upper

_ALLOWED_SEPARATORS = frozenset({"", "-"})
_ALLOWED_GENERATION_POLICIES = frozenset(
    {"AUTO_REQUIRED", "AUTO_DEFAULT", "MANUAL_ONLY"}
)


class CodigoSecuenciaRead(BaseModel):
    """Detalle / ítem de listado de secuencia cfg (enriquecido con Catalog)."""

    secuencia_id: UUID
    sequence_key: str
    scope_type: str
    scope_fingerprint: str
    empresa_id: Optional[UUID] = None
    almacen_id: Optional[UUID] = None
    punto_venta_id: Optional[UUID] = None
    prefijo: str
    separador: str
    longitud_numero: int
    numero_inicial: int
    ultimo_numero: int
    es_activo: bool
    generation_policy: str
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime] = None
    usuario_actualizacion_id: Optional[UUID] = None
    entity_table: Optional[str] = None
    code_column: Optional[str] = None
    modulo_codigo: Optional[str] = None
    catalog_policy: Optional[str] = None
    supports_preview: Optional[bool] = None
    allow_manual: Optional[bool] = None
    sequence_family: Optional[str] = None
    default_prefix: Optional[str] = None
    default_separator: Optional[str] = None
    default_padding: Optional[int] = None
    config_locked: bool
    policy_drift: bool

    class Config:
        from_attributes = True


class CodigoSecuenciaUpdate(BaseModel):
    """PATCH — campos de formato + generation_policy (sin es_activo)."""

    model_config = ConfigDict(extra="forbid")

    prefijo: Optional[str] = Field(None, max_length=10)
    separador: Optional[str] = None
    longitud_numero: Optional[int] = Field(None, ge=1)
    numero_inicial: Optional[int] = Field(None, ge=1)
    generation_policy: Optional[str] = None

    @field_validator("prefijo", mode="before")
    @classmethod
    def _normalize_prefijo(cls, v: Optional[str]) -> Optional[str]:
        return normalize_upper(v)

    @field_validator("separador", mode="before")
    @classmethod
    def _normalize_separador(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return normalize_strip(v) if isinstance(v, str) else v

    @field_validator("separador")
    @classmethod
    def _validate_separador(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        if v not in _ALLOWED_SEPARATORS:
            raise ValueError("separador solo admite cadena vacía o '-'")
        return v

    @field_validator("generation_policy", mode="before")
    @classmethod
    def _normalize_generation_policy(cls, v: Optional[str]) -> Optional[str]:
        return normalize_upper(v) if isinstance(v, str) or v is None else v

    @field_validator("generation_policy")
    @classmethod
    def _validate_generation_policy(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        if v not in _ALLOWED_GENERATION_POLICIES:
            raise ValueError(
                "generation_policy solo admite AUTO_REQUIRED, AUTO_DEFAULT o MANUAL_ONLY"
            )
        return v


class CodigoSecuenciaPreviewResponse(BaseModel):
    """Resultado de preview — no consume correlativo."""

    secuencia_id: UUID
    sequence_key: str
    codigo_estimado: str
    ultimo_numero_actual: int
    numero_inicial: int
    consume_contador: bool = False
    es_activo: bool
    disclaimer: str


class PaginatedCodigoSecuenciaResponse(ErpPaginatedResponse[CodigoSecuenciaRead]):
    """Envelope paginado ERP (opt-in con query param page)."""

    pass
