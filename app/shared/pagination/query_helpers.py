"""Helpers SQLAlchemy Core para paginación y ordenamiento ERP."""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, TypeVar

from sqlalchemy import asc, desc
from sqlalchemy.sql import ColumnElement, Select

from app.core.exceptions import CustomException
from app.shared.pagination.params import ErpPaginationParams

T = TypeVar("T", bound=Select)

SortOrderItem = tuple[ColumnElement[Any], str]


def apply_erp_pagination(
    query: T,
    pagination: ErpPaginationParams,
) -> T:
    """Aplica OFFSET/LIMIT solo en modo paginado."""
    if not pagination.is_paginated:
        return query
    return query.offset(pagination.offset).limit(pagination.limit)


def extract_count(result: List[Dict[str, Any]]) -> int:
    """Extrae entero de fila COUNT devuelta por execute_query."""
    if not result:
        return 0
    row = result[0]
    return int(row.get("count_1") or row.get("count") or next(iter(row.values()), 0))


def _direction_clause(column: ColumnElement[Any], direction: str):
    if direction == "desc":
        return desc(column)
    return asc(column)


def apply_erp_sort(
    query: T,
    *,
    allowed_columns: frozenset[str],
    column_map: Mapping[str, ColumnElement[Any]],
    sort_by: Optional[str],
    sort_dir: Optional[str],
    default_order: Sequence[SortOrderItem],
    tie_breaker: Optional[tuple[str, ColumnElement[Any]]] = None,
    column_dir_defaults: Optional[Mapping[str, str]] = None,
) -> T:
    """
    Aplica ORDER BY server-side con whitelist.
    Sin sort_by → default_order exacto (compatibilidad legacy).
    sort_by inválido → ValidationError 422.
    """
    if not sort_by:
        clauses = [_direction_clause(col, direction) for col, direction in default_order]
        return query.order_by(*clauses)

    if sort_by not in allowed_columns or sort_by not in column_map:
        raise CustomException(
            status_code=422,
            detail=f"sort_by '{sort_by}' no es una columna ordenable válida.",
            internal_code="INVALID_SORT_COLUMN",
        )

    effective_dir = sort_dir
    if effective_dir is None:
        effective_dir = (column_dir_defaults or {}).get(sort_by, "asc")

    clauses = [_direction_clause(column_map[sort_by], effective_dir)]
    if tie_breaker is not None:
        tie_name, tie_col = tie_breaker
        if tie_name != sort_by:
            clauses.append(asc(tie_col))
    return query.order_by(*clauses)


def apply_memory_sort(
    rows: List[Dict[str, Any]],
    *,
    allowed_columns: frozenset[str],
    sort_by: Optional[str],
    sort_dir: Optional[str],
    default_key: Callable[[Dict[str, Any]], Any],
    tie_breaker_key: Callable[[Dict[str, Any]], Any],
    column_dir_defaults: Optional[Mapping[str, str]] = None,
) -> List[Dict[str, Any]]:
    """Ordenamiento en memoria para listas híbridas (ej. parámetros ORG)."""
    if not sort_by:
        return sorted(rows, key=lambda r: (default_key(r), tie_breaker_key(r)))

    if sort_by not in allowed_columns:
        raise CustomException(
            status_code=422,
            detail=f"sort_by '{sort_by}' no es una columna ordenable válida.",
            internal_code="INVALID_SORT_COLUMN",
        )

    effective_dir = sort_dir
    if effective_dir is None:
        effective_dir = (column_dir_defaults or {}).get(sort_by, "asc")
    reverse = effective_dir == "desc"

    def _sort_key(row: Dict[str, Any]):
        primary = row.get(sort_by)
        return (primary is None, primary, tie_breaker_key(row))

    return sorted(rows, key=_sort_key, reverse=reverse)
