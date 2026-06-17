"""Schemas de respuesta paginada ERP."""
from __future__ import annotations

from typing import Generic, List, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErpPaginatedResponse(BaseModel, Generic[T]):
    """Envelope canónico ERP: items + metadatos de paginación."""

    items: List[T] = Field(..., description="Registros de la página actual")
    total: int = Field(..., ge=0, description="Total de registros que coinciden con filtros")
    pagina_actual: int = Field(..., ge=1, description="Página solicitada")
    total_paginas: int = Field(..., ge=0, description="Total de páginas disponibles")
    limit: int = Field(..., ge=1, le=100, description="Tamaño de página efectivo")

    class Config:
        from_attributes = True
