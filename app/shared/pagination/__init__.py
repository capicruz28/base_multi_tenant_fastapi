"""Infraestructura compartida de paginación ERP (ORG/INV)."""
from app.shared.pagination.schemas import ErpPaginatedResponse
from app.shared.pagination.params import (
    DEFAULT_LIMIT,
    MAX_LIMIT,
    ErpPaginationParams,
    erp_pagination_params,
)
from app.shared.pagination.sort import ErpSortParams, erp_sort_params
from app.shared.pagination.builder import build_paginated_response, calc_total_paginas
from app.shared.pagination.response_mode import is_paginated_mode

__all__ = [
    "ErpPaginatedResponse",
    "DEFAULT_LIMIT",
    "MAX_LIMIT",
    "ErpPaginationParams",
    "erp_pagination_params",
    "ErpSortParams",
    "erp_sort_params",
    "build_paginated_response",
    "calc_total_paginas",
    "is_paginated_mode",
]
