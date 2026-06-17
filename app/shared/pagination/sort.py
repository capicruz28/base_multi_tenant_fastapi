"""Parámetros de ordenamiento ERP — opt-in por presencia de sort_by."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

from fastapi import Query

SortDirection = Literal["asc", "desc"]


@dataclass(frozen=True)
class ErpSortParams:
    """Ordenamiento server-side. sort_dir sin sort_by se ignora."""

    sort_by: Optional[str]
    sort_dir: Optional[SortDirection]

    @property
    def is_active(self) -> bool:
        return self.sort_by is not None


def erp_sort_params(
    sort_by: Optional[str] = Query(
        None,
        description="Columna whitelist para ordenar (ver documentación del recurso).",
    ),
    sort_dir: Optional[SortDirection] = Query(
        None,
        description="Dirección de orden: asc o desc. Solo aplica con sort_by.",
    ),
) -> ErpSortParams:
    """sort_dir sin sort_by se ignora (compatibilidad legacy)."""
    if sort_by is None:
        return ErpSortParams(sort_by=None, sort_dir=None)
    return ErpSortParams(sort_by=sort_by, sort_dir=sort_dir)
