"""
DedicatedCatalogSeedService — bootstrap_v2 S6 catálogos en BD Dedicated (PR-F4-06).

Aplica S010–S066 según perfil plan con markers ``bootstrap_applied``.
Desacoplado — consumo exclusivo por orchestrator F4-08.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Optional

from app.core.exceptions import ConflictError, DatabaseError, ValidationError
from app.infrastructure.provisioning.catalog_profiles import (
    CatalogSeedScriptEntry,
    dedupe_row_expectations,
    discover_catalog_scripts,
    normalize_plan_suscripcion,
    resolve_catalog_seed_profile,
    validate_catalog_profile_integrity,
)
from app.infrastructure.provisioning.dedicated_catalog_seed_types import (
    CatalogRowVerification,
    DedicatedCatalogSeedRequest,
    DedicatedCatalogSeedResult,
)
from app.infrastructure.provisioning.dedicated_database_naming import (
    assert_sql_identifier,
    escape_sql_literal,
)
from app.infrastructure.provisioning.dedicated_ddl_client import (
    DedicatedDdlClient,
    create_default_ddl_client,
)
from app.infrastructure.provisioning.dedicated_permission_catalog_sync_service import (
    DedicatedPermissionCatalogSyncService,
)
from app.infrastructure.provisioning.dedicated_permission_catalog_sync_types import (
    DedicatedPermissionCatalogSyncRequest,
)
from app.infrastructure.provisioning.script_manifest import split_sql_server_batches

logger = logging.getLogger(__name__)

_TABLE_NAME_RE = re.compile(r"^[A-Za-z0-9_]{1,128}$")
_STEP_CODE = "apply_catalogs"


class DedicatedCatalogSeedService:
    """Ejecutor seed catálogos bootstrap_v2 para perfil plan Dedicated S6."""

    def __init__(
        self,
        ddl_client: Optional[DedicatedDdlClient] = None,
        *,
        bootstrap_root: Path | None = None,
        permission_catalog_sync: Optional[DedicatedPermissionCatalogSyncService] = None,
    ) -> None:
        self._ddl = ddl_client
        self._bootstrap_root = bootstrap_root
        self._permission_catalog_sync = permission_catalog_sync

    def _client(self) -> DedicatedDdlClient:
        if self._ddl is not None:
            return self._ddl
        return create_default_ddl_client()

    async def run_catalog_seed(
        self,
        request: DedicatedCatalogSeedRequest,
    ) -> DedicatedCatalogSeedResult:
        assert_sql_identifier(request.database_name, field="database_name")
        plan = normalize_plan_suscripcion(request.plan_suscripcion)
        profile = resolve_catalog_seed_profile(plan)
        validate_catalog_profile_integrity(profile, bootstrap_root=self._bootstrap_root)

        discovered = discover_catalog_scripts(
            profile,
            bootstrap_root=self._bootstrap_root,
        )

        executed: list[str] = []
        skipped: list[str] = []
        batches_executed = 0

        for entry, script_path, checksum in discovered:
            applied = await self._is_script_applied(
                request.database_name,
                entry.script_code,
                checksum,
            )
            if applied:
                logger.info(
                    "Catalog seed skipped cliente_id=%s database=%s script=%s",
                    request.cliente_id,
                    request.database_name,
                    entry.script_code,
                )
                skipped.append(entry.script_code)
                continue

            batches_executed += await self._execute_script_file(
                request.database_name,
                script_path,
            )
            await self._record_script_applied(
                request.database_name,
                entry,
                checksum,
            )
            executed.append(entry.script_code)
            logger.info(
                "Catalog seed applied cliente_id=%s database=%s script=%s plan=%s",
                request.cliente_id,
                request.database_name,
                entry.script_code,
                plan,
            )

        row_verifications = await self._verify_row_expectations(
            request.database_name,
            dedupe_row_expectations(profile.row_expectations),
        )

        sync_status: Optional[str] = None
        sync_hash: Optional[str] = None
        sync_inserted = 0
        sync_updated = 0
        sync_deactivated = 0

        from app.core.config import settings

        if settings.DEDICATED_PERMISSION_CATALOG_SYNC_ENABLED:
            sync_service = (
                self._permission_catalog_sync
                or DedicatedPermissionCatalogSyncService()
            )
            sync_result = await sync_service.run_sync(
                DedicatedPermissionCatalogSyncRequest(
                    database_name=request.database_name,
                    cliente_id=request.cliente_id,
                    provisioning_run_id=request.provisioning_run_id,
                )
            )
            sync_status = sync_result.status
            sync_hash = sync_result.registry_hash or None
            sync_inserted = sync_result.inserted
            sync_updated = sync_result.updated
            sync_deactivated = sync_result.deactivated

        return DedicatedCatalogSeedResult(
            database_name=request.database_name,
            cliente_id=request.cliente_id,
            plan_suscripcion=plan,
            profile_code=profile.profile_code,
            scripts_executed=tuple(executed),
            scripts_skipped=tuple(skipped),
            batches_executed=batches_executed,
            row_verifications=row_verifications,
            permission_catalog_sync_status=sync_status,
            permission_catalog_sync_registry_hash=sync_hash,
            permission_catalog_sync_inserted=sync_inserted,
            permission_catalog_sync_updated=sync_updated,
            permission_catalog_sync_deactivated=sync_deactivated,
        )

    async def _is_script_applied(
        self,
        database_name: str,
        script_code: str,
        checksum: str,
    ) -> bool:
        escaped_code = escape_sql_literal(script_code)
        stored = await self._client().scalar_str(
            f"SELECT checksum_sha256 FROM bootstrap_applied "
            f"WHERE script_code = N'{escaped_code}'",
            database=database_name,
        )
        if stored is None:
            return False
        if stored.lower() == checksum.lower():
            return True
        raise ConflictError(
            detail=(
                f"Marker bootstrap_applied divergente para catálogo {script_code}."
            ),
            internal_code="CATALOG_MARKER_CHECKSUM_MISMATCH",
        )

    async def _execute_script_file(
        self,
        database_name: str,
        script_path: Path,
    ) -> int:
        content = script_path.read_text(encoding="utf-8-sig")
        batches = split_sql_server_batches(content)
        if not batches:
            raise ValidationError(
                detail=f"Script catálogo sin batches ejecutables: {script_path.name}.",
                internal_code="CATALOG_SCRIPT_NO_BATCHES",
            )
        executed = 0
        for batch in batches:
            try:
                await self._client().execute(batch, database=database_name)
            except DatabaseError as exc:
                raise ConflictError(
                    detail="Error aplicando seed catálogo en BD dedicada.",
                    internal_code="PROVISIONING_CATALOG_FAILED",
                ) from exc
            executed += 1
        return executed

    async def _record_script_applied(
        self,
        database_name: str,
        entry: CatalogSeedScriptEntry,
        checksum: str,
    ) -> None:
        escaped_code = escape_sql_literal(entry.script_code)
        escaped_path = escape_sql_literal(entry.relative_path)
        escaped_checksum = escape_sql_literal(checksum)
        escaped_step = escape_sql_literal(_STEP_CODE)
        sql = (
            "INSERT INTO bootstrap_applied "
            "(script_code, script_path, checksum_sha256, step_code) "
            f"VALUES (N'{escaped_code}', N'{escaped_path}', "
            f"N'{escaped_checksum}', N'{escaped_step}');"
        )
        try:
            await self._client().execute(sql, database=database_name)
        except DatabaseError as exc:
            raise ConflictError(
                detail="No se pudo registrar marker catálogo bootstrap_applied.",
                internal_code="CATALOG_MARKER_INSERT_FAILED",
            ) from exc

    async def _verify_row_expectations(
        self,
        database_name: str,
        expectations: tuple[tuple[str, int], ...],
    ) -> tuple[CatalogRowVerification, ...]:
        results: list[CatalogRowVerification] = []
        for table_name, min_rows in expectations:
            if not _TABLE_NAME_RE.match(table_name):
                raise ValidationError(
                    detail=f"Nombre de tabla catálogo inválido: {table_name}.",
                    internal_code="INVALID_CATALOG_TABLE_NAME",
                )
            count = await self._client().scalar_int(
                f"SELECT COUNT(*) FROM [{table_name}]",
                database=database_name,
            )
            if count is None:
                count = 0
            if count < min_rows:
                raise ConflictError(
                    detail=(
                        f"Verificación catálogo insuficiente en {table_name}: "
                        f"esperado>={min_rows}, actual={count}."
                    ),
                    internal_code="CATALOG_ROW_COUNT_FAILED",
                )
            results.append(
                CatalogRowVerification(
                    table_name=table_name,
                    row_count=count,
                    min_rows=min_rows,
                )
            )
        return tuple(results)


__all__ = ["DedicatedCatalogSeedService"]
