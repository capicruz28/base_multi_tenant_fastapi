"""
Lookup de usuarios platform/SYSTEM en bd_sistema (single-DB).

get_connection_for_tenant(SYSTEM) fuerza conexión ADMIN; los operadores platform
(platform_admin) viven en la misma BD que tenants (DEFAULT + cliente_id SYSTEM).
Misma regla que AuthService._fetch_user_row_for_refresh.
"""
from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import and_, select

from app.core.config import settings
from app.infrastructure.database.connection_async import DatabaseConnection
from app.infrastructure.database.queries_async import execute_auth_query, execute_query
from app.infrastructure.database.tables import UsuarioTable


def system_cliente_id() -> Optional[UUID]:
    if not settings.SUPERADMIN_CLIENTE_ID:
        return None
    try:
        return UUID(str(settings.SUPERADMIN_CLIENTE_ID))
    except (ValueError, TypeError):
        return None


def is_system_request_client(request_cliente_id: Optional[UUID]) -> bool:
    sid = system_cliente_id()
    return sid is not None and request_cliente_id == sid


async def fetch_platform_usuario_row(
    username: str,
    *,
    cliente_id: UUID,
) -> Optional[Dict[str, Any]]:
    """
    Fallback: usuario SYSTEM en bd_sistema cuando no está en ADMIN.
    Debe devolver todas las columnas de usuario (UsuarioRead).
    """
    user_query = select(UsuarioTable).where(
        and_(
            UsuarioTable.c.nombre_usuario == username,
            UsuarioTable.c.cliente_id == cliente_id,
            UsuarioTable.c.es_eliminado == False,
        )
    )
    rows = await execute_query(
        user_query,
        connection_type=DatabaseConnection.DEFAULT,
        client_id=cliente_id,
    )
    return rows[0] if rows else None


async def fetch_usuario_auth_row(
    user_query: Any,
    *,
    username: str,
    request_cliente_id: Optional[UUID],
) -> Optional[Dict[str, Any]]:
    """
    Resuelve fila usuario para auth deps.

    SYSTEM: primero execute_auth_query (ADMIN, fila completa); si no existe,
    fallback bd_sistema. No devolver columnas parciales (rompe UsuarioReadWithRoles).
    """
    if is_system_request_client(request_cliente_id):
        row = await execute_auth_query(user_query)
        if row:
            return row
        if request_cliente_id:
            return await fetch_platform_usuario_row(
                username, cliente_id=request_cliente_id
            )
        return None
    return await execute_auth_query(user_query)


def resolve_platform_superadmin_flag(
    *,
    username: str,
    request_cliente_id: Optional[UUID],
    roles_result: Optional[list],
    nivel_acceso: int,
    is_superadmin_from_roles: bool,
) -> bool:
    """Operador platform: cross-tenant y privilegios de impersonación."""
    if is_superadmin_from_roles:
        return True
    if not is_system_request_client(request_cliente_id):
        return False
    if username == settings.SUPERADMIN_USERNAME:
        return True
    for role in roles_result or []:
        codigo = (role.get("codigo_rol") or "").upper()
        nivel = role.get("nivel_acceso") or 0
        if codigo in ("SUPER_ADMIN", "ADMIN_PLATFORM") and nivel >= 5:
            return True
    return nivel_acceso >= 5
