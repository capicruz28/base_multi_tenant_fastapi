"""
Normalización de rutas de menú para el contrato FE SaaS.

Legacy catálogo: /org/*, /inv/*
Contrato FE: /app/org/*, /app/inv/*
Admin tenant: /admin/* (ya en S020)
Platform: /super-admin/* (ya en S020)
"""
from __future__ import annotations

from typing import Optional

_RESERVED_PREFIXES = ("/app/", "/admin/", "/super-admin/", "/api")


def normalize_menu_ruta_for_fe(ruta: Optional[str]) -> Optional[str]:
    """
    Devuelve la ruta lista para el router del frontend.

    - Ya normalizada (/app/, /admin/, /super-admin/) → sin cambios
    - Legacy ERP absoluto (/org/..., /inv/...) → prefijo /app
    """
    if ruta is None:
        return None
    if not isinstance(ruta, str):
        return ruta
    path = ruta.strip()
    if not path:
        return path
    if not path.startswith("/"):
        return path
    lower = path.lower()
    for prefix in _RESERVED_PREFIXES:
        if lower.startswith(prefix):
            return path
    return f"/app{path}"
