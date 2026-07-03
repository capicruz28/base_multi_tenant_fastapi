"""
DedicatedPermissionCatalogSyncService — réplica PermissionRegistry en BD Dedicated (F12-B).

Ejecutado al final de S6 (post apply_catalogs, pre S7). Idempotente vía bootstrap_applied.
"""
from __future__ import annotations

import logging
from contextlib import AbstractAsyncContextManager
from typing import Any, Callable, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authorization.permission_catalog_sync_core import (
    compute_registry_hash,
    sync_permission_catalog,
)
from app.core.authorization.permission_catalog_sync_types import SyncMode
from app.core.authorization.permission_metadata import PermissionMetadata
from app.core.authorization.permission_startup import populate_permission_registry
from app.core.config import settings
from app.core.exceptions import ConflictError, DatabaseError
from app.infrastructure.provisioning.dedicated_database_naming import assert_sql_identifier, escape_sql_literal
from app.infrastructure.provisioning.dedicated_permission_catalog_sync_types import (
    DedicatedPermissionCatalogSyncRequest,
    DedicatedPermissionCatalogSyncResult,
)
from app.infrastructure.provisioning.provisioning_dedicated_session import provisioning_dedicated_session

logger = logging.getLogger(__name__)

SCRIPT_CODE = "permission_catalog_sync"
STEP_CODE = "permission_catalog_sync"
SCRIPT_PATH = "permission_catalog_sync/registry"

DedicatedSessionFactory = Callable[[str], AbstractAsyncContextManager[AsyncSession]]


class _DedicatedCatalogExecutor:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def fetch_existing(self) -> list[dict]:
        result = await self._session.execute(
            text("SELECT permiso_id, codigo FROM permiso")
        )
        return [
            {"permiso_id": str(row[0]), "codigo": str(row[1])}
            for row in result.fetchall()
        ]

    async def resolve_modulo_id(self, modulo_codigo: str) -> Optional[str]:
        if not modulo_codigo or not modulo_codigo.strip():
            return None
        result = await self._session.execute(
            text(
                "SELECT modulo_id FROM modulo "
                "WHERE codigo = :codigo AND es_activo = 1"
            ),
            {"codigo": modulo_codigo.strip()},
        )
        row = result.fetchone()
        return str(row[0]) if row else None

    async def insert_permiso(
        self,
        *,
        permiso_id: str,
        codigo: str,
        nombre: str,
        descripcion: Optional[str],
        modulo_id: Optional[str],
        recurso: str,
        accion: str,
    ) -> None:
        await self._session.execute(
            text(
                "INSERT INTO permiso "
                "(permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo) "
                "VALUES (:permiso_id, :codigo, :nombre, :descripcion, :modulo_id, :recurso, :accion, 1)"
            ),
            {
                "permiso_id": permiso_id,
                "codigo": codigo,
                "nombre": nombre,
                "descripcion": descripcion,
                "modulo_id": modulo_id,
                "recurso": recurso,
                "accion": accion,
            },
        )

    async def update_permiso(
        self,
        *,
        codigo: str,
        nombre: str,
        descripcion: Optional[str],
        modulo_id: Optional[str],
        recurso: str,
        accion: str,
    ) -> None:
        await self._session.execute(
            text(
                "UPDATE permiso "
                "SET nombre = :nombre, descripcion = :descripcion, modulo_id = :modulo_id, "
                "recurso = :recurso, accion = :accion, es_activo = 1, "
                "fecha_actualizacion = GETDATE() "
                "WHERE codigo = :codigo"
            ),
            {
                "codigo": codigo,
                "nombre": nombre,
                "descripcion": descripcion,
                "modulo_id": modulo_id,
                "recurso": recurso,
                "accion": accion,
            },
        )

    async def deactivate_permiso(self, codigo: str) -> None:
        await self._session.execute(
            text(
                "UPDATE permiso "
                "SET es_activo = 0, fecha_actualizacion = GETDATE() "
                "WHERE codigo = :codigo"
            ),
            {"codigo": codigo},
        )


class DedicatedPermissionCatalogSyncService:
    """Réplica read-only del PermissionRegistry en permiso (Dedicated Data Plane)."""

    def __init__(
        self,
        session_factory: Optional[DedicatedSessionFactory] = None,
    ) -> None:
        self._session_factory = session_factory or provisioning_dedicated_session

    async def run_sync(
        self,
        request: DedicatedPermissionCatalogSyncRequest,
        *,
        app: Any = None,
        declared: Optional[list[PermissionMetadata]] = None,
    ) -> DedicatedPermissionCatalogSyncResult:
        assert_sql_identifier(request.database_name, field="database_name")

        if not settings.DEDICATED_PERMISSION_CATALOG_SYNC_ENABLED:
            logger.info(
                "Permission catalog sync disabled cliente_id=%s database=%s",
                request.cliente_id,
                request.database_name,
            )
            return DedicatedPermissionCatalogSyncResult(
                database_name=request.database_name,
                cliente_id=request.cliente_id,
                status="disabled",
                registry_hash="",
            )

        resolved_declared = self._resolve_declared(app=app, declared=declared)
        registry_hash = compute_registry_hash(resolved_declared)

        async with self._session_factory(request.database_name) as session:
            if await self._is_sync_applied(session, registry_hash):
                logger.info(
                    "Permission catalog sync skipped cliente_id=%s database=%s hash=%s",
                    request.cliente_id,
                    request.database_name,
                    registry_hash[:12],
                )
                return DedicatedPermissionCatalogSyncResult(
                    database_name=request.database_name,
                    cliente_id=request.cliente_id,
                    status="skipped",
                    registry_hash=registry_hash,
                    declared_count=len(resolved_declared),
                )

            try:
                result = await sync_permission_catalog(
                    declared=resolved_declared,
                    executor=_DedicatedCatalogExecutor(session),
                    mode=SyncMode.DEDICATED_DATA_PLANE,
                )
            except Exception as exc:
                raise ConflictError(
                    detail="Error sincronizando catálogo permisos en BD dedicada.",
                    internal_code="PROVISIONING_PERMISSION_CATALOG_SYNC_FAILED",
                ) from exc

            await self._upsert_sync_marker(session, registry_hash)

        logger.info(
            "Permission catalog sync applied cliente_id=%s database=%s "
            "inserted=%s updated=%s deactivated=%s declared=%s",
            request.cliente_id,
            request.database_name,
            result.inserted,
            result.updated,
            result.deactivated,
            result.declared_count,
        )
        return DedicatedPermissionCatalogSyncResult(
            database_name=request.database_name,
            cliente_id=request.cliente_id,
            status="applied",
            registry_hash=registry_hash,
            inserted=result.inserted,
            updated=result.updated,
            deactivated=result.deactivated,
            declared_count=result.declared_count,
        )

    @staticmethod
    def _resolve_declared(
        *,
        app: Any,
        declared: Optional[list[PermissionMetadata]],
    ) -> list[PermissionMetadata]:
        if declared is not None:
            return declared
        resolved_app = app
        if resolved_app is None:
            from app.main import app as fastapi_app

            resolved_app = fastapi_app
        return populate_permission_registry(resolved_app)

    async def _is_sync_applied(
        self,
        session: AsyncSession,
        registry_hash: str,
    ) -> bool:
        escaped_code = escape_sql_literal(SCRIPT_CODE)
        result = await session.execute(
            text(
                f"SELECT checksum_sha256 FROM bootstrap_applied "
                f"WHERE script_code = N'{escaped_code}'"
            )
        )
        row = result.fetchone()
        if row is None:
            return False
        stored = str(row[0] or "")
        return stored.lower() == registry_hash.lower()

    async def _upsert_sync_marker(
        self,
        session: AsyncSession,
        registry_hash: str,
    ) -> None:
        escaped_code = escape_sql_literal(SCRIPT_CODE)
        escaped_path = escape_sql_literal(SCRIPT_PATH)
        escaped_checksum = escape_sql_literal(registry_hash)
        escaped_step = escape_sql_literal(STEP_CODE)

        existing = await session.execute(
            text(
                f"SELECT 1 FROM bootstrap_applied WHERE script_code = N'{escaped_code}'"
            )
        )
        if existing.fetchone() is not None:
            await session.execute(
                text(
                    "UPDATE bootstrap_applied "
                    f"SET checksum_sha256 = N'{escaped_checksum}', "
                    f"script_path = N'{escaped_path}', "
                    f"step_code = N'{escaped_step}' "
                    f"WHERE script_code = N'{escaped_code}'"
                )
            )
            return

        try:
            await session.execute(
                text(
                    "INSERT INTO bootstrap_applied "
                    "(script_code, script_path, checksum_sha256, step_code) "
                    f"VALUES (N'{escaped_code}', N'{escaped_path}', "
                    f"N'{escaped_checksum}', N'{escaped_step}')"
                )
            )
        except DatabaseError as exc:
            raise ConflictError(
                detail="No se pudo registrar marker permission_catalog_sync.",
                internal_code="PERMISSION_CATALOG_SYNC_MARKER_FAILED",
            ) from exc


__all__ = [
    "DedicatedPermissionCatalogSyncService",
    "SCRIPT_CODE",
    "STEP_CODE",
]
