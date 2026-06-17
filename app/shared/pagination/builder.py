"""Helpers para construir respuestas paginadas ERP."""
from __future__ import annotations

import math
from typing import List, TypeVar

from app.shared.pagination.params import ErpPaginationParams
from app.shared.pagination.schemas import ErpPaginatedResponse

T = TypeVar("T")


def calc_total_paginas(total: int, limit: int) -> int:
    """Calcula total de páginas. total=0 → 0 páginas."""
    if total <= 0:
        return 0
    return math.ceil(total / limit)


def build_paginated_response(
    items: List[T],
    total: int,
    pagination: ErpPaginationParams,
) -> ErpPaginatedResponse[T]:
    """Construye envelope ERP a partir de items, total y parámetros de paginación."""
    page = pagination.page or 1
    return ErpPaginatedResponse(
        items=items,
        total=total,
        pagina_actual=page,
        total_paginas=calc_total_paginas(total, pagination.limit),
        limit=pagination.limit,
    )
