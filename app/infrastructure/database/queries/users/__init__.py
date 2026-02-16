"""
Queries de gestión de usuarios.

✅ FASE 2: Queries migradas desde sql_constants.py

Este módulo contiene:
- Queries de listado y paginación de usuarios
- Queries de búsqueda de usuarios
- Queries de creación/actualización de usuarios
"""

from .user_queries import (
    SELECT_USUARIOS_PAGINATED,
    COUNT_USUARIOS_PAGINATED,
    SELECT_USUARIOS_PAGINATED_MULTI_DB,
    COUNT_USUARIOS_PAGINATED_MULTI_DB,
    GET_USER_COMPLETE_OPTIMIZED_JSON,
    GET_USER_COMPLETE_OPTIMIZED_XML,
)

__all__ = [
    "SELECT_USUARIOS_PAGINATED",
    "COUNT_USUARIOS_PAGINATED",
    "SELECT_USUARIOS_PAGINATED_MULTI_DB",
    "COUNT_USUARIOS_PAGINATED_MULTI_DB",
    "GET_USER_COMPLETE_OPTIMIZED_JSON",
    "GET_USER_COMPLETE_OPTIMIZED_XML",
]
