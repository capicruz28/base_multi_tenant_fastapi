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
from uuid import uuid4

from sqlalchemy import text

from app.core.authorization.permission_registry import get_all
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update
from app.infrastructure.database.connection_async import DatabaseConnection

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
    except Exception as e:
        logger.debug("%s Resolución modulo_codigo->modulo_id (no bloqueante): %s", RBAC_LOG_PREFIX, e)
    return None


async def sync() -> None:
    """
    Sincroniza permisos del registry con la tabla permiso.
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

    codigos_declared = {p["codigo"] for p in declared}

    # 1) Mapa modulo_codigo -> modulo_id
    modulo_ids: dict[str, str | None] = {}
    for p in declared:
        mc = p.get("modulo_codigo")
        if mc and mc not in modulo_ids:
            modulo_ids[mc] = await _get_modulo_id_by_codigo(mc)
    if None in modulo_ids:
        modulo_ids[None] = None

    # 2) Leer tabla permiso (BD central)
    try:
        sql_existing = text("SELECT permiso_id, codigo FROM permiso")
        existing_rows = await execute_query(
            sql_existing,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None,
        )
    except Exception as e:
        logger.warning("%s No se pudo leer tabla permiso (sync omitido): %s", RBAC_LOG_PREFIX, e)
        return

    existing_by_codigo = {r["codigo"]: r for r in (existing_rows or [])}

    # 3) INSERT o UPDATE por cada declarado
    for p in declared:
        codigo = p["codigo"]
        nombre = (p.get("nombre") or codigo)[:150]
        descripcion = (p.get("descripcion") or "")[:500] or None
        recurso = (p.get("recurso") or "")[:80]
        accion = (p.get("accion") or "")[:30]
        modulo_codigo = p.get("modulo_codigo")
        modulo_id = modulo_ids.get(modulo_codigo) if modulo_codigo else None

        if codigo not in existing_by_codigo:
            try:
                permiso_id = str(uuid4())
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
                logger.info("%s Permission synced: %s", RBAC_LOG_PREFIX, codigo)
            except Exception as e:
                logger.warning("%s Error insertando permiso %s: %s", RBAC_LOG_PREFIX, codigo, e)
        else:
            try:
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
                logger.info("%s Permission synced: %s", RBAC_LOG_PREFIX, codigo)
            except Exception as e:
                logger.warning("%s Error actualizando permiso %s: %s", RBAC_LOG_PREFIX, codigo, e)

    # 4) Desactivar permisos que están en BD pero no en código
    for codigo, row in existing_by_codigo.items():
        if codigo not in codigos_declared:
            try:
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
                logger.info("%s Permission disabled: %s", RBAC_LOG_PREFIX, codigo)
            except Exception as e:
                logger.warning("%s Error desactivando permiso %s: %s", RBAC_LOG_PREFIX, codigo, e)
