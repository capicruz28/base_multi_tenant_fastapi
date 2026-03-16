# app/modules/rbac/application/services/permisos_usuario_service.py
"""
Servicio para obtener los códigos de permiso de negocio (RBAC) de un usuario.

Usa las tablas permiso (BD central) y rol_permiso (tenant: central o dedicada).
No modifica rol_menu_permiso ni el flujo de menú existente.

Filtro por módulos contratados: cuando filter_by_active_modules=True, solo se devuelven
permisos cuyo permiso.modulo_id es NULL (globales: admin, modulos) o pertenece a un
módulo activo del tenant en cliente_modulo (esta_activo=1, fecha_vencimiento vigente).
"""

from typing import List
from uuid import UUID
import logging
from sqlalchemy import text

from app.infrastructure.database.queries_async import execute_query
from app.infrastructure.database.connection_async import DatabaseConnection

logger = logging.getLogger(__name__)

# Fragmento SQL: restricción por módulos activos del tenant (cliente_modulo).
# Incluye permisos globales (modulo_id IS NULL) y de módulos contratados.
_CLIENTE_MODULO_FILTER = """
      AND (
          p.modulo_id IS NULL
          OR EXISTS (
              SELECT 1 FROM cliente_modulo cm
              WHERE cm.modulo_id = p.modulo_id
                AND cm.cliente_id = :cliente_id
                AND cm.esta_activo = 1
                AND (cm.fecha_vencimiento IS NULL OR cm.fecha_vencimiento > CAST(GETDATE() AS DATE))
          )
      )
"""


async def obtener_codigos_permiso_usuario(
    usuario_id: UUID,
    cliente_id: UUID,
    database_type: str = "single",
    *,
    filter_by_active_modules: bool = True,
) -> List[str]:
    """
    Obtiene la lista de códigos de permiso (ej. admin.usuario.leer) que tiene
    el usuario por sus roles, desde permiso + rol_permiso.

    Flujo: Usuario → Roles (usuario_rol) → Permisos (rol_permiso ⋈ permiso)
           → Módulos contratados (cliente_modulo) → Permisos finales.

    filter_by_active_modules=True (por defecto): solo retorna permisos cuyo
    permiso.modulo_id es NULL o está en cliente_modulo activos del tenant.
    """
    try:
        if database_type == "multi":
            return await _permisos_dedicated(usuario_id, cliente_id, filter_by_active_modules)
        return await _permisos_single(usuario_id, cliente_id, filter_by_active_modules)
    except Exception as e:
        logger.warning(
            f"[PERMISOS_USUARIO] Error obteniendo permisos para usuario {usuario_id}: {e}. "
            "Devolviendo lista vacía para no romper auth."
        )
        return []


async def _permisos_single(
    usuario_id: UUID, cliente_id: UUID, filter_by_active_modules: bool
) -> List[str]:
    """BD central/shared: permiso y rol_permiso en la misma BD. Filtro por cliente_modulo si está activo."""
    sql = text("""
        SELECT DISTINCT p.codigo
        FROM usuario_rol ur
        INNER JOIN rol_permiso rp ON rp.rol_id = ur.rol_id AND rp.cliente_id = ur.cliente_id
        INNER JOIN permiso p ON p.permiso_id = rp.permiso_id AND p.es_activo = 1
        WHERE ur.usuario_id = :usuario_id
          AND ur.cliente_id = :cliente_id
          AND ur.es_activo = 1
          AND (ur.fecha_expiracion IS NULL OR ur.fecha_expiracion > GETDATE())
    """ + (_CLIENTE_MODULO_FILTER if filter_by_active_modules else "") + "\n").bindparams(
        usuario_id=usuario_id, cliente_id=cliente_id
    )

    rows = await execute_query(
        sql,
        client_id=cliente_id,
        connection_type=DatabaseConnection.DEFAULT,
        skip_tenant_validation=False,
    )
    if not rows:
        return []
    return [r["codigo"] for r in rows if r.get("codigo")]


async def _permisos_dedicated(
    usuario_id: UUID, cliente_id: UUID, filter_by_active_modules: bool
) -> List[str]:
    """BD dedicada: rol_permiso en tenant; permiso en central (ADMIN). Filtro por cliente_modulo en central."""
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

    # 2) Códigos desde BD central (permiso), filtrando por módulos activos del tenant (cliente_modulo)
    placeholders = ", ".join(f":p{i}" for i in range(len(permiso_ids)))
    if filter_by_active_modules:
        sql_codigos = text(
            f"""
            SELECT codigo FROM permiso p
            WHERE p.es_activo = 1 AND p.permiso_id IN ({placeholders})
              AND (
                  p.modulo_id IS NULL
                  OR EXISTS (
                      SELECT 1 FROM cliente_modulo cm
                      WHERE cm.modulo_id = p.modulo_id
                        AND cm.cliente_id = :cliente_id
                        AND cm.esta_activo = 1
                        AND (cm.fecha_vencimiento IS NULL OR cm.fecha_vencimiento > CAST(GETDATE() AS DATE))
                  )
              )
            """
        )
        params = {f"p{i}": pid for i, pid in enumerate(permiso_ids)}
        params["cliente_id"] = cliente_id
        sql_codigos = sql_codigos.bindparams(**params)
    else:
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
