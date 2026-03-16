from __future__ import annotations

import logging
from typing import List
from uuid import UUID

from app.infrastructure.database.connection_async import DatabaseConnection
from app.infrastructure.database.queries_async import execute_query
from sqlalchemy import text

logger = logging.getLogger(__name__)

RBAC_LOG_PREFIX = "[RBAC]"


def _infer_recurso_from_menu_codigo(menu_codigo: str | None) -> str | None:
    if not menu_codigo or not isinstance(menu_codigo, str):
        return None
    parts = menu_codigo.strip().split("_")
    if not parts:
        return None
    return parts[-1].lower()


def _match_recurso(menu_recurso: str, permiso_recurso: str) -> bool:
    if not menu_recurso or not permiso_recurso:
        return False
    if menu_recurso == permiso_recurso:
        return True
    if menu_recurso.rstrip("s") == permiso_recurso or menu_recurso == permiso_recurso.rstrip("s"):
        return True
    return False


async def resolve_required_permissions_for_menu_tree(modulos: List) -> None:
    """
    Enriquecer en memoria el árbol de menú asignando required_permission por menú tipo 'pantalla'.
    No persiste nada en BD.
    """
    if not modulos:
        return

    # Recoger pares (modulo_id, recurso_inferido) de todos los menús tipo pantalla
    pairs: set[tuple[UUID, str]] = set()

    for modulo in modulos:
        modulo_id = getattr(modulo, "modulo_id", None)
        if not modulo_id:
            continue
        for seccion in getattr(modulo, "secciones", []) or []:
            for menu in getattr(seccion, "menus", []) or []:
                if getattr(menu, "tipo_menu", "pantalla") != "pantalla":
                    continue
                codigo = getattr(menu, "codigo", None)
                recurso = _infer_recurso_from_menu_codigo(codigo)
                if not recurso:
                    continue
                pairs.add((modulo_id, recurso))

    if not pairs:
        return

    modulo_ids = list({mid for mid, _ in pairs})

    # Cargar permisos de lectura por modulo_id desde BD central (SQL raw, sin tabla mapeada)
    placeholders = ",".join(f":mid{i}" for i in range(len(modulo_ids)))
    params = {f"mid{i}": str(mid) for i, mid in enumerate(modulo_ids)}
    sql = text(
        f"""
        SELECT codigo, modulo_id, recurso
        FROM permiso
        WHERE es_activo = 1
          AND accion = 'leer'
          AND modulo_id IN ({placeholders})
        """
    ).bindparams(**params)

    rows = await execute_query(
        sql,
        connection_type=DatabaseConnection.ADMIN,
        client_id=None,
    )

    if not rows:
        logger.debug("%s MenuPermissionResolver: no se encontraron permisos leer para modulos %s", RBAC_LOG_PREFIX, modulo_ids)
        return

    # Índice por (modulo_id, recurso_normalizado)
    by_modulo_recurso: dict[tuple[str, str], str] = {}
    for r in rows:
        mid = r.get("modulo_id")
        recurso = (r.get("recurso") or "").strip().lower()
        codigo = (r.get("codigo") or "").strip()
        if not mid or not codigo or not recurso:
            continue
        mid_key = str(mid)
        by_modulo_recurso[(mid_key, recurso)] = codigo
        if recurso.endswith("s"):
            by_modulo_recurso[(mid_key, recurso.rstrip("s"))] = codigo
        else:
            by_modulo_recurso[(mid_key, recurso + "s")] = codigo

    # Asignar required_permission en memoria
    for modulo in modulos:
        modulo_id = getattr(modulo, "modulo_id", None)
        if not modulo_id:
            continue
        for seccion in getattr(modulo, "secciones", []) or []:
            for menu in getattr(seccion, "menus", []) or []:
                try:
                    if getattr(menu, "tipo_menu", "pantalla") != "pantalla":
                        continue
                    codigo_menu = getattr(menu, "codigo", None)
                    recurso_menu = _infer_recurso_from_menu_codigo(codigo_menu)
                    if not recurso_menu:
                        continue
                    permiso_codigo = None
                    for (mid_key, recurso_key), cod in by_modulo_recurso.items():
                        if str(modulo_id) != mid_key:
                            continue
                        if _match_recurso(recurso_menu, recurso_key):
                            permiso_codigo = cod
                            break
                    if permiso_codigo:
                        setattr(menu, "required_permission", permiso_codigo)
                    else:
                        if getattr(menu, "required_permission", None) is None:
                            logger.warning(
                                "%s MenuPermissionResolver: no se encontró permiso leer para menú %s (modulo_id=%s, recurso=%s)",
                                RBAC_LOG_PREFIX,
                                codigo_menu or getattr(menu, "menu_id", None),
                                modulo_id,
                                recurso_menu,
                            )
                except Exception as e:
                    logger.debug("%s MenuPermissionResolver: error resolviendo menú %s: %s", RBAC_LOG_PREFIX, getattr(menu, "codigo", None), e)

