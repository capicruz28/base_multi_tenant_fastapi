# app/modules/rbac/application/services/permisos_usuario_service.py
"""
Servicio para obtener los códigos de permiso de negocio (RBAC) de un usuario.

Usa las tablas permiso (BD central) y rol_permiso (tenant: central o dedicada).
No modifica rol_menu_permiso ni el flujo de menú existente.
"""

from typing import List
from uuid import UUID
import logging
from sqlalchemy import text

from app.infrastructure.database.queries_async import execute_query
from app.infrastructure.database.connection_async import DatabaseConnection

logger = logging.getLogger(__name__)


async def obtener_codigos_permiso_usuario(
    usuario_id: UUID,
    cliente_id: UUID,
    database_type: str = "single",
) -> List[str]:
    """
    Obtiene la lista de códigos de permiso (ej. admin.usuario.leer) que tiene
    el usuario por sus roles, desde permiso + rol_permiso.

    - Single DB: una sola query (usuario_rol + rol_permiso + permiso en misma BD).
    - Multi DB: query en tenant (usuario_rol + rol_permiso) y luego en central
      (permiso) para resolver códigos.

    No rompe si las tablas no existen o están vacías: devuelve [].
    """
    try:
        if database_type == "multi":
            return await _permisos_dedicated(usuario_id, cliente_id)
        return await _permisos_single(usuario_id, cliente_id)
    except Exception as e:
        logger.warning(
            f"[PERMISOS_USUARIO] Error obteniendo permisos para usuario {usuario_id}: {e}. "
            "Devolviendo lista vacía para no romper auth."
        )
        return []


async def _permisos_single(usuario_id: UUID, cliente_id: UUID) -> List[str]:
    """BD central/shared: permiso y rol_permiso en la misma BD."""
    sql = text("""
        SELECT DISTINCT p.codigo
        FROM usuario_rol ur
        INNER JOIN rol_permiso rp ON rp.rol_id = ur.rol_id AND rp.cliente_id = ur.cliente_id
        INNER JOIN permiso p ON p.permiso_id = rp.permiso_id AND p.es_activo = 1
        WHERE ur.usuario_id = :usuario_id
          AND ur.cliente_id = :cliente_id
          AND ur.es_activo = 1
          AND (ur.fecha_expiracion IS NULL OR ur.fecha_expiracion > GETDATE())
    """).bindparams(usuario_id=usuario_id, cliente_id=cliente_id)

    rows = await execute_query(
        sql,
        client_id=cliente_id,
        connection_type=DatabaseConnection.DEFAULT,
        skip_tenant_validation=False,
    )
    if not rows:
        return []
    return [r["codigo"] for r in rows if r.get("codigo")]


async def _permisos_dedicated(usuario_id: UUID, cliente_id: UUID) -> List[str]:
    """BD dedicada: rol_permiso en tenant; permiso solo en central (ADMIN)."""
    # 1) Permiso IDs desde BD del tenant (sin tabla permiso)
    sql_ids = text("""
        SELECT DISTINCT rp.permiso_id
        FROM usuario_rol ur
        INNER JOIN rol_permiso rp ON rp.rol_id = ur.rol_id AND rp.cliente_id = ur.cliente_id
        WHERE ur.usuario_id = :usuario_id
          AND ur.cliente_id = :cliente_id
          AND ur.es_activo = 1
          AND (ur.fecha_expiracion IS NULL OR ur.fecha_expiracion > GETDATE())
    """).bindparams(usuario_id=usuario_id, cliente_id=cliente_id)

    rows_ids = await execute_query(
        sql_ids,
        client_id=cliente_id,
        connection_type=DatabaseConnection.DEFAULT,
        skip_tenant_validation=False,
    )
    if not rows_ids:
        return []

    permiso_ids = [r["permiso_id"] for r in rows_ids if r.get("permiso_id")]
    if not permiso_ids:
        return []

    # 2) Códigos desde BD central (permiso)
    # permiso está en GLOBAL_TABLES, no se aplica filtro tenant
    placeholders = ", ".join(f":p{i}" for i in range(len(permiso_ids)))
    sql_codigos = text(
        f"SELECT codigo FROM permiso WHERE es_activo = 1 AND permiso_id IN ({placeholders})"
    )
    params = {f"p{i}": pid for i, pid in enumerate(permiso_ids)}
    sql_codigos = sql_codigos.bindparams(**params)

    rows_codigos = await execute_query(
        sql_codigos,
        connection_type=DatabaseConnection.ADMIN,
        skip_tenant_validation=False,
    )
    if not rows_codigos:
        return []
    return [r["codigo"] for r in rows_codigos if r.get("codigo")]
