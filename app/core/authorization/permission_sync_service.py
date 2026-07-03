# app/core/authorization/permission_sync_service.py
"""
Sincroniza permisos declarados en código (PermissionRegistry) con la tabla permiso (BD central).
Se ejecuta al startup. Idempotente: puede ejecutarse múltiples veces sin duplicar datos.

Reglas:
- codigo no existe en BD → INSERT
- codigo existe → UPDATE metadata (nombre, descripcion, recurso, accion, modulo_id, es_activo=1)
- codigo existe en BD pero no en código → es_activo=0
"""
from __future__ import annotations

import logging

from sqlalchemy import text

from app.core.authorization.permission_catalog_sync_core import sync_permission_catalog
from app.core.authorization.permission_catalog_sync_types import SyncMode
from app.core.authorization.permission_registry import get_all
from app.infrastructure.database.connection_async import DatabaseConnection
from app.infrastructure.database.queries_async import execute_insert, execute_query, execute_update

logger = logging.getLogger(__name__)

RBAC_LOG_PREFIX = "[RBAC]"


async def _get_modulo_id_by_codigo(modulo_codigo: str | None) -> str | None:
    """Obtiene modulo_id desde tabla modulo (BD central) por codigo. Retorna None si no existe."""
    if not modulo_codigo or not modulo_codigo.strip():
        return None
    try:
        sql = text("""
            SELECT modulo_id FROM modulo
            WHERE codigo = :codigo AND es_activo = 1
        """).bindparams(codigo=modulo_codigo.strip())
        rows = await execute_query(
            sql,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None,
        )
        if rows and len(rows) > 0:
            return str(rows[0].get("modulo_id"))
    except Exception as exc:
        logger.debug(
            "%s Resolución modulo_codigo->modulo_id (no bloqueante): %s",
            RBAC_LOG_PREFIX,
            exc,
        )
    return None


class _ControlPlaneCatalogExecutor:
    async def fetch_existing(self) -> list[dict]:
        sql_existing = text("SELECT permiso_id, codigo FROM permiso")
        rows = await execute_query(
            sql_existing,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None,
        )
        return list(rows or [])

    async def resolve_modulo_id(self, modulo_codigo: str) -> str | None:
        return await _get_modulo_id_by_codigo(modulo_codigo)

    async def insert_permiso(
        self,
        *,
        permiso_id: str,
        codigo: str,
        nombre: str,
        descripcion: str | None,
        modulo_id: str | None,
        recurso: str,
        accion: str,
    ) -> None:
        ins = text("""
            INSERT INTO permiso (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
            VALUES (:permiso_id, :codigo, :nombre, :descripcion, :modulo_id, :recurso, :accion, 1)
        """).bindparams(
            permiso_id=permiso_id,
            codigo=codigo,
            nombre=nombre,
            descripcion=descripcion,
            modulo_id=modulo_id,
            recurso=recurso,
            accion=accion,
        )
        await execute_insert(
            ins,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None,
        )

    async def update_permiso(
        self,
        *,
        codigo: str,
        nombre: str,
        descripcion: str | None,
        modulo_id: str | None,
        recurso: str,
        accion: str,
    ) -> None:
        upd = text("""
            UPDATE permiso
            SET nombre = :nombre, descripcion = :descripcion, modulo_id = :modulo_id,
                recurso = :recurso, accion = :accion, es_activo = 1, fecha_actualizacion = GETDATE()
            WHERE codigo = :codigo
        """).bindparams(
            codigo=codigo,
            nombre=nombre,
            descripcion=descripcion,
            modulo_id=modulo_id,
            recurso=recurso,
            accion=accion,
        )
        await execute_update(
            upd,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None,
        )

    async def deactivate_permiso(self, codigo: str) -> None:
        upd_disabled = text("""
            UPDATE permiso
            SET es_activo = 0, fecha_actualizacion = GETDATE()
            WHERE codigo = :codigo
        """).bindparams(codigo=codigo)
        await execute_update(
            upd_disabled,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None,
        )


async def sync() -> None:
    """
    Sincroniza permisos del registry con la tabla permiso (Control Plane).
    Idempotente.
    """
    try:
        from app.core.config import settings

        if getattr(settings, "RBAC_PERMISSION_SYNC_ENABLED", True) is False:
            logger.info("%s Permission sync deshabilitado por configuración.", RBAC_LOG_PREFIX)
            return
    except Exception:
        pass

    declared = get_all()
    if not declared:
        logger.info("%s No hay permisos declarados en código para sincronizar.", RBAC_LOG_PREFIX)
        return

    try:
        result = await sync_permission_catalog(
            declared=declared,
            executor=_ControlPlaneCatalogExecutor(),
            mode=SyncMode.CONTROL_PLANE,
        )
        logger.info(
            "%s Permission sync summary: declared=%s, inserted=%s, updated=%s, deactivated=%s",
            RBAC_LOG_PREFIX,
            result.declared_count,
            result.inserted,
            result.updated,
            result.deactivated,
        )
    except Exception as exc:
        logger.warning("%s No se pudo sincronizar tabla permiso (sync omitido): %s", RBAC_LOG_PREFIX, exc)
