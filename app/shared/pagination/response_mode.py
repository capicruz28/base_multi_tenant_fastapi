"""Resolución de modo de respuesta listado ERP."""
from __future__ import annotations

from typing import Optional


def is_paginated_mode(page: Optional[int]) -> bool:
    """True si el cliente solicitó modo paginado (page presente)."""
    return page is not None
