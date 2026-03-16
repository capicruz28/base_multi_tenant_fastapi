# app/core/authorization/menu_permission_binder.py
"""
Vincula menús tipo "pantalla" con permisos de lectura (accion='leer').
Regla: required_permission = "{modulo}.{recurso}.leer" según permiso en BD.
Solo actualiza modulo_menu.permiso_codigo_requerido cuando está NULL (no sobrescribe valor manual).
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import text

from app.infrastructure.database.queries_async import execute_query, execute_update
from app.infrastructure.database.connection_async import DatabaseConnection

logger = logging.getLogger(__name__)

RBAC_LOG_PREFIX = "[RBAC]"


def _recurso_from_menu_codigo(menu_codigo: str | None) -> str | None:
    """Deriva recurso desde menu.codigo (ej. LOG_RUTAS -> rutas)."""
    if not menu_codigo or not isinstance(menu_codigo, str):
        return None
    parts = menu_codigo.strip().split("_")
    if not parts:
        return None
    return parts[-1].lower()


def _match_recurso(menu_recurso: str, permiso_recurso: str) -> bool:
    """True si menu_recurso coincide con permiso_recurso (rutas/ruta, areas/area)."""
    if not menu_recurso or not permiso_recurso:
        return False
    if menu_recurso == permiso_recurso:
        return True
    if menu_recurso.rstrip("s") == permiso_recurso or menu_recurso == permiso_recurso.rstrip("s"):
        return True
    return False


async def bind() -> None:
    """
    Busca permisos con accion='leer', mapea recurso ↔ menu.codigo,
    actualiza modulo_menu.permiso_codigo_requerido solo si está NULL.
    """
    try:
        # 1) Permisos con accion='leer' (codigo, modulo_id, recurso)
        sql_permisos = text("""
            SELECT codigo, modulo_id, recurso
            FROM permiso
            WHERE es_activo = 1 AND accion = 'leer'
        """)
        rows_perm = await execute_query(
            sql_permisos,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None,
        )
        if not rows_perm:
            logger.debug("%s No hay permisos con accion=leer para binding.", RBAC_LOG_PREFIX)
            return

        # 2) Menús tipo pantalla con permiso_codigo_requerido NULL o vacío
        sql_menus = text("""
            SELECT m.menu_id, m.modulo_id, m.codigo AS menu_codigo, m.permiso_codigo_requerido
            FROM modulo_menu m
            INNER JOIN modulo mod ON mod.modulo_id = m.modulo_id
            WHERE m.tipo_menu = 'pantalla'
              AND m.es_activo = 1
              AND (m.permiso_codigo_requerido IS NULL OR LTRIM(RTRIM(m.permiso_codigo_requerido)) = '')
        """)
        rows_menus = await execute_query(
            sql_menus,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None,
        )
        if not rows_menus:
            logger.debug("%s No hay menús sin permiso para binding.", RBAC_LOG_PREFIX)
            return

        # Map (modulo_id, recurso) -> permiso.codigo (permiso.recurso puede ser 'ruta', menu tiene 'rutas')
        by_modulo_recurso: dict[tuple[Any, str], str] = {}
        for r in rows_perm:
            mid = r.get("modulo_id")
            recurso = (r.get("recurso") or "").strip().lower()
            codigo = (r.get("codigo") or "").strip()
            if mid and codigo:
                by_modulo_recurso[(str(mid), recurso)] = codigo
                if recurso.endswith("s"):
                    by_modulo_recurso[(str(mid), recurso.rstrip("s"))] = codigo
                else:
                    by_modulo_recurso[(str(mid), recurso + "s")] = codigo

        bound_count = 0
        for menu in rows_menus:
            menu_id = menu.get("menu_id")
            modulo_id = menu.get("modulo_id")
            menu_codigo = (menu.get("menu_codigo") or "").strip()
            if not menu_id or not modulo_id:
                continue
            recurso_candidate = _recurso_from_menu_codigo(menu_codigo)
            if not recurso_candidate:
                continue
            # Buscar permiso que coincida (modulo_id + recurso)
            permiso_codigo = None
            for (mid_key, rec_key), cod in by_modulo_recurso.items():
                if str(modulo_id) != str(mid_key):
                    continue
                if _match_recurso(recurso_candidate, rec_key):
                    permiso_codigo = cod
                    break
            if not permiso_codigo:
                continue
            try:
                upd = text("""
                    UPDATE modulo_menu
                    SET permiso_codigo_requerido = :codigo, fecha_actualizacion = GETDATE()
                    WHERE menu_id = :menu_id
                """).bindparams(codigo=permiso_codigo, menu_id=str(menu_id))
                await execute_update(upd, connection_type=DatabaseConnection.ADMIN, client_id=None)
                logger.info("%s Menu bound: %s → %s", RBAC_LOG_PREFIX, menu_codigo or menu_id, permiso_codigo)
                bound_count += 1
            except Exception as e:
                logger.debug("%s Error binding menu %s: %s", RBAC_LOG_PREFIX, menu_id, e)

        if bound_count:
            logger.info("%s MenuPermissionBinder: %d menús vinculados.", RBAC_LOG_PREFIX, bound_count)
    except Exception as e:
        logger.warning("%s MenuPermissionBinder.bind failed: %s", RBAC_LOG_PREFIX, e)
        raise
