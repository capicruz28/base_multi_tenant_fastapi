"""Motor compartido — sync PermissionRegistry → tabla permiso (F12-B)."""
from __future__ import annotations

import hashlib
import json
import logging
from typing import Iterable, Optional
from uuid import uuid4

from app.core.authorization.core_permissions import (
    DEDICATED_PROTECTED_PERMISSION_CODIGOS,
    DEDICATED_SYNC_MANAGED_PREFIXES,
    PROTECTED_PERMISSION_CODIGOS,
)
from app.core.authorization.permission_catalog_sync_types import (
    PermissionCatalogExecutor,
    SyncMode,
    SyncResult,
)
from app.core.authorization.permission_metadata import PermissionMetadata

logger = logging.getLogger(__name__)

RBAC_LOG_PREFIX = "[RBAC]"


def compute_registry_hash(declared: Iterable[PermissionMetadata]) -> str:
    """Hash estable del catálogo declarado (codigo + metadata relevante)."""
    canonical = [
        {
            "codigo": p["codigo"],
            "nombre": p.get("nombre"),
            "recurso": p.get("recurso"),
            "accion": p.get("accion"),
            "modulo_codigo": p.get("modulo_codigo"),
        }
        for p in sorted(declared, key=lambda item: item["codigo"])
    ]
    payload = json.dumps(canonical, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def should_deactivate_permiso(
    codigo: str,
    codigos_declared: set[str],
    mode: SyncMode,
) -> bool:
    if codigo in codigos_declared:
        return False
    if codigo in PROTECTED_PERMISSION_CODIGOS:
        return False
    if mode == SyncMode.DEDICATED_DATA_PLANE:
        if codigo in DEDICATED_PROTECTED_PERMISSION_CODIGOS:
            return False
        if not any(codigo.startswith(prefix) for prefix in DEDICATED_SYNC_MANAGED_PREFIXES):
            return False
    return True


async def sync_permission_catalog(
    *,
    declared: list[PermissionMetadata],
    executor: PermissionCatalogExecutor,
    mode: SyncMode,
) -> SyncResult:
    if not declared:
        logger.info("%s Permission catalog sync: catálogo vacío.", RBAC_LOG_PREFIX)
        return SyncResult(declared_count=0)

    codigos_declared = {p["codigo"] for p in declared}
    modulo_ids: dict[str | None, Optional[str]] = {}

    for perm in declared:
        mc = perm.get("modulo_codigo")
        if mc not in modulo_ids:
            modulo_ids[mc] = await executor.resolve_modulo_id(mc) if mc else None

    existing_rows = await executor.fetch_existing()
    existing_by_codigo = {row["codigo"]: row for row in existing_rows}

    inserted = 0
    updated = 0
    deactivated = 0

    for perm in declared:
        codigo = perm["codigo"]
        nombre = (perm.get("nombre") or codigo)[:150]
        descripcion = (perm.get("descripcion") or "")[:500] or None
        recurso = (perm.get("recurso") or "")[:80]
        accion = (perm.get("accion") or "")[:30]
        modulo_codigo = perm.get("modulo_codigo")
        modulo_id = modulo_ids.get(modulo_codigo) if modulo_codigo else None

        if codigo not in existing_by_codigo:
            try:
                await executor.insert_permiso(
                    permiso_id=str(uuid4()),
                    codigo=codigo,
                    nombre=nombre,
                    descripcion=descripcion,
                    modulo_id=modulo_id,
                    recurso=recurso,
                    accion=accion,
                )
                inserted += 1
                logger.info("%s Permission catalog inserted: %s", RBAC_LOG_PREFIX, codigo)
            except Exception as exc:
                logger.warning(
                    "%s Error insertando permiso %s: %s",
                    RBAC_LOG_PREFIX,
                    codigo,
                    exc,
                )
        else:
            try:
                await executor.update_permiso(
                    codigo=codigo,
                    nombre=nombre,
                    descripcion=descripcion,
                    modulo_id=modulo_id,
                    recurso=recurso,
                    accion=accion,
                )
                updated += 1
                logger.info("%s Permission catalog updated: %s", RBAC_LOG_PREFIX, codigo)
            except Exception as exc:
                logger.warning(
                    "%s Error actualizando permiso %s: %s",
                    RBAC_LOG_PREFIX,
                    codigo,
                    exc,
                )

    for codigo in existing_by_codigo:
        if not should_deactivate_permiso(codigo, codigos_declared, mode):
            continue
        try:
            await executor.deactivate_permiso(codigo)
            deactivated += 1
            logger.info("%s Permission catalog disabled: %s", RBAC_LOG_PREFIX, codigo)
        except Exception as exc:
            logger.warning(
                "%s Error desactivando permiso %s: %s",
                RBAC_LOG_PREFIX,
                codigo,
                exc,
            )

    return SyncResult(
        inserted=inserted,
        updated=updated,
        deactivated=deactivated,
        declared_count=len(declared),
    )


__all__ = [
    "compute_registry_hash",
    "should_deactivate_permiso",
    "sync_permission_catalog",
]
