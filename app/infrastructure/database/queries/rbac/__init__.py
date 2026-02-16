"""
Queries de RBAC (Roles y Permisos).

✅ FASE 2: Queries migradas desde sql_constants.py

Este módulo contiene:
- Queries de roles
- Queries de permisos
- Queries de asignación de roles a usuarios
"""

from .rbac_queries import (
    SELECT_ROLES_PAGINATED,
    COUNT_ROLES_PAGINATED,
    SELECT_PERMISOS_POR_ROL,
    DEACTIVATE_ROL,
    REACTIVATE_ROL,
    DELETE_PERMISOS_POR_ROL,
    INSERT_PERMISO_ROL,
)

__all__ = [
    "SELECT_ROLES_PAGINATED",
    "COUNT_ROLES_PAGINATED",
    "SELECT_PERMISOS_POR_ROL",
    "DEACTIVATE_ROL",
    "REACTIVATE_ROL",
    "DELETE_PERMISOS_POR_ROL",
    "INSERT_PERMISO_ROL",
]
