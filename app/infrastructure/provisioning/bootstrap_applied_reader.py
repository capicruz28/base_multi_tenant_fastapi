"""Lectura markers bootstrap_applied en DP — reconciliación S4/S5 (PR-F4-08 / H-02)."""
from __future__ import annotations

from typing import Optional

from app.infrastructure.provisioning.dedicated_database_naming import escape_sql_literal
from app.infrastructure.provisioning.dedicated_ddl_client import (
    DedicatedDdlClient,
    create_default_ddl_client,
)
from app.infrastructure.provisioning.script_manifest import (
    DEDICATED_SCHEMA_MANIFEST_V2,
    load_dedicated_schema_manifest,
)

_BOOTSTRAP_SCRIPT_CODES: tuple[str, ...] = tuple(
    entry.script_code
    for entry in sorted(
        load_dedicated_schema_manifest(
            profile=DEDICATED_SCHEMA_MANIFEST_V2.profile,
        ).entries,
        key=lambda item: item.execution_order,
    )
)


class BootstrapAppliedReader:
    """Consulta read-only de scripts aplicados en BD dedicada."""

    def __init__(self, ddl_client: Optional[DedicatedDdlClient] = None) -> None:
        self._ddl = ddl_client

    def _client(self) -> DedicatedDdlClient:
        if self._ddl is not None:
            return self._ddl
        return create_default_ddl_client()

    async def list_applied_script_codes(self, database_name: str) -> frozenset[str]:
        applied: set[str] = set()
        for script_code in _BOOTSTRAP_SCRIPT_CODES:
            escaped = escape_sql_literal(script_code)
            stored = await self._client().scalar_str(
                f"SELECT checksum_sha256 FROM bootstrap_applied "
                f"WHERE script_code = N'{escaped}'",
                database=database_name,
            )
            if stored:
                applied.add(script_code)
        return frozenset(applied)


__all__ = ["BootstrapAppliedReader", "_BOOTSTRAP_SCRIPT_CODES"]
