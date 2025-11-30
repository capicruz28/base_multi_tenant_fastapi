# app/infrastructure/database/__init__.py
"""
Infraestructura de base de datos: conexiones, queries, repositorios
"""

from app.infrastructure.database.connection import (
    get_db_connection,
    DatabaseConnection,
    get_connection_string
)

from app.infrastructure.database.queries import (
    execute_query,
    execute_auth_query,
    execute_insert,
    execute_update
)

__all__ = [
    "get_db_connection",
    "DatabaseConnection",
    "get_connection_string",
    "execute_query",
    "execute_auth_query",
    "execute_insert",
    "execute_update"
]

