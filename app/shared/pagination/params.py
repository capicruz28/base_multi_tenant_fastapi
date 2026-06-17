"""Parámetros de paginación ERP — opt-in por presencia de page."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fastapi import Query

DEFAULT_LIMIT = 50
MAX_LIMIT = 100


@dataclass(frozen=True)
class ErpPaginationParams:
    """Parámetros de paginación. page=None → modo legacy (sin COUNT/OFFSET)."""

    page: Optional[int]
    limit: int

    @property
    def is_paginated(self) -> bool:
        return self.page is not None

    @property
    def offset(self) -> int:
        if self.page is None:
            return 0
        return (self.page - 1) * self.limit


def erp_pagination_params(
    page: Optional[int] = Query(
        None,
        ge=1,
        description="Si se envía, activa respuesta paginada (envelope ERP).",
    ),
    limit: Optional[int] = Query(
        None,
        ge=1,
        le=MAX_LIMIT,
        description=f"Tamaño de página (solo aplica con page). Default {DEFAULT_LIMIT}, máx {MAX_LIMIT}.",
    ),
) -> ErpPaginationParams:
    """
    limit sin page se ignora (compatibilidad legacy).
    Con page presente, limit default = DEFAULT_LIMIT.
    """
    effective_limit = limit if limit is not None else DEFAULT_LIMIT
    return ErpPaginationParams(page=page, limit=effective_limit)
