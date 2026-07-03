"""
BootstrapScriptRunner — bootstrap_v2 S4–S5 en BD Dedicated (PR-F4-05 / F4-05b / F12-G3).

Aplica V010 ERP + DTSP + rol_permiso + auth_audit_log con markers ``bootstrap_applied``.
Verificación post-run: ``DEDICATED_RUNTIME_REQUIRED_TABLES``.
Desacoplado — consumo exclusivo por orchestrator F4-08.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from app.core.exceptions import ConflictError, DatabaseError, ValidationError
from app.infrastructure.provisioning.bootstrap_script_types import (
    BootstrapScriptRunRequest,
    BootstrapScriptRunResult,
)
from app.infrastructure.provisioning.dedicated_database_naming import (
    assert_sql_identifier,
    escape_sql_literal,
)
from app.infrastructure.provisioning.dedicated_ddl_client import (
    DedicatedDdlClient,
    create_default_ddl_client,
)
from app.infrastructure.provisioning.script_manifest import (
    DEDICATED_RUNTIME_REQUIRED_TABLES,
    DEDICATED_SCHEMA_MANIFEST_V2,
    BootstrapScriptManifest,
    BootstrapScriptManifestEntry,
    discover_manifest_entries,
    load_dedicated_schema_manifest,
    split_sql_server_batches,
    validate_manifest_integrity,
)

logger = logging.getLogger(__name__)

_BOOTSTRAP_APPLIED_DDL = """
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = N'bootstrap_applied')
BEGIN
    CREATE TABLE bootstrap_applied (
        bootstrap_applied_id UNIQUEIDENTIFIER NOT NULL
            CONSTRAINT PK_bootstrap_applied PRIMARY KEY DEFAULT NEWID(),
        script_code NVARCHAR(64) NOT NULL,
        script_path NVARCHAR(512) NOT NULL,
        checksum_sha256 CHAR(64) NOT NULL,
        step_code NVARCHAR(32) NOT NULL,
        applied_at DATETIME2 NOT NULL CONSTRAINT DF_bootstrap_applied_applied_at
            DEFAULT SYSUTCDATETIME(),
        CONSTRAINT UQ_bootstrap_applied_script_code UNIQUE (script_code)
    );
END
"""


class BootstrapScriptRunner:
    """Ejecutor secuencial bootstrap_v2 para perfil dedicated schema v2 (DTSP)."""

    def __init__(
        self,
        ddl_client: Optional[DedicatedDdlClient] = None,
        *,
        bootstrap_root: Path | None = None,
    ) -> None:
        self._ddl = ddl_client
        self._bootstrap_root = bootstrap_root

    def _client(self) -> DedicatedDdlClient:
        if self._ddl is not None:
            return self._ddl
        return create_default_ddl_client()

    async def run_dedicated_schema_bootstrap(
        self,
        request: BootstrapScriptRunRequest,
    ) -> BootstrapScriptRunResult:
        assert_sql_identifier(request.database_name, field="database_name")
        manifest = load_dedicated_schema_manifest(profile=request.profile)
        validate_manifest_integrity(manifest, bootstrap_root=self._bootstrap_root)

        await self._ensure_bootstrap_applied_table(request.database_name)

        discovered = discover_manifest_entries(
            manifest,
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
                    "Bootstrap script skipped cliente_id=%s database=%s script=%s",
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
                "Bootstrap script applied cliente_id=%s database=%s script=%s step=%s",
                request.cliente_id,
                request.database_name,
                entry.script_code,
                entry.step_code,
            )

        if manifest.profile == DEDICATED_SCHEMA_MANIFEST_V2.profile:
            await self._verify_runtime_schema(request.database_name)

        return BootstrapScriptRunResult(
            database_name=request.database_name,
            cliente_id=request.cliente_id,
            profile=manifest.profile,
            scripts_executed=tuple(executed),
            scripts_skipped=tuple(skipped),
            batches_executed=batches_executed,
        )

    async def _verify_runtime_schema(self, database_name: str) -> None:
        """Fail-fast post-run — tablas runtime obligatorias (DTSP + audit + ERP mínimo)."""
        missing: list[str] = []
        for table_name in sorted(DEDICATED_RUNTIME_REQUIRED_TABLES):
            escaped = escape_sql_literal(table_name)
            exists = await self._client().scalar_int(
                f"SELECT CASE WHEN OBJECT_ID(N'dbo.{escaped}', N'U') IS NOT NULL "
                f"THEN 1 ELSE 0 END",
                database=database_name,
            )
            if not exists:
                missing.append(table_name)
        if missing:
            raise ConflictError(
                detail=(
                    "Schema dedicated incompleto tras bootstrap runtime: "
                    f"faltan tablas {', '.join(missing)}."
                ),
                internal_code="PROVISIONING_SCHEMA_FAILED",
            )

    async def _ensure_bootstrap_applied_table(self, database_name: str) -> None:
        try:
            await self._client().execute(
                _BOOTSTRAP_APPLIED_DDL,
                database=database_name,
            )
        except DatabaseError as exc:
            raise ConflictError(
                detail="No se pudo inicializar tabla bootstrap_applied.",
                internal_code="BOOTSTRAP_MARKER_TABLE_FAILED",
            ) from exc

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
                f"Marker bootstrap_applied divergente para script {script_code}."
            ),
            internal_code="BOOTSTRAP_MARKER_CHECKSUM_MISMATCH",
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
                detail=f"Script bootstrap sin batches ejecutables: {script_path.name}.",
                internal_code="BOOTSTRAP_SCRIPT_NO_BATCHES",
            )
        executed = 0
        for batch in batches:
            try:
                await self._client().execute(batch, database=database_name)
            except DatabaseError as exc:
                raise ConflictError(
                    detail="Error aplicando script bootstrap en BD dedicada.",
                    internal_code="PROVISIONING_SCHEMA_FAILED",
                ) from exc
            executed += 1
        return executed

    async def _record_script_applied(
        self,
        database_name: str,
        entry: BootstrapScriptManifestEntry,
        checksum: str,
    ) -> None:
        escaped_code = escape_sql_literal(entry.script_code)
        escaped_path = escape_sql_literal(entry.relative_path)
        escaped_checksum = escape_sql_literal(checksum)
        escaped_step = escape_sql_literal(entry.step_code)
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
                detail="No se pudo registrar marker bootstrap_applied.",
                internal_code="BOOTSTRAP_MARKER_INSERT_FAILED",
            ) from exc


__all__ = ["BootstrapScriptRunner"]
