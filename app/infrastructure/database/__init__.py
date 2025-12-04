# app/infrastructure/database/__init__.py
"""
Infraestructura de base de datos: conexiones, queries, repositorios

✅ FASE 2: Actualizado para exportar versiones async
- Todas las funciones exportadas son async
- Usa SQLAlchemy AsyncSession
"""

# ✅ FASE 2: Exportar desde connection_async (versiones async)
from app.infrastructure.database.connection_async import (
    get_db_connection,
    DatabaseConnection,
)

# ✅ FASE 2: Exportar desde queries_async (versiones async)
from app.infrastructure.database.queries_async import (
    execute_query,
    execute_auth_query,
    execute_insert,
    execute_update,
)

__all__ = [
    "get_db_connection",
    "DatabaseConnection",
    "execute_query",
    "execute_auth_query",
    "execute_insert",
    "execute_update"
]

