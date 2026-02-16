"""
Queries de auditoría.

✅ FASE 2: Queries migradas desde sql_constants.py

Este módulo contiene:
- Queries de logs de autenticación
- Queries de logs de sincronización
- Queries de auditoría general
"""

from .audit_queries import (
    INSERT_AUTH_AUDIT_LOG,
    INSERT_LOG_SINCRONIZACION_USUARIO,
)

__all__ = [
    "INSERT_AUTH_AUDIT_LOG",
    "INSERT_LOG_SINCRONIZACION_USUARIO",
]
