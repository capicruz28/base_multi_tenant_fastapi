#!/usr/bin/env python3
"""
F12-G3 — Validación E2E bootstrap Dedicated (read-only probes + bootstrap runner).

Ejecutar dentro del contenedor backend:
  python scripts/f12_g3_validate_dedicated_e2e.py

Crea BD dedicada efímera, aplica manifiesto v2.1 completo y verifica
DEDICATED_RUNTIME_REQUIRED_TABLES sin tenants legacy (acce/acces/acmec).
"""
from __future__ import annotations

import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone

# Asegurar /app en path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.infrastructure.provisioning.bootstrap_script_runner import BootstrapScriptRunner
from app.infrastructure.provisioning.bootstrap_script_types import BootstrapScriptRunRequest
from app.infrastructure.provisioning.dedicated_ddl_client import create_default_ddl_client
from app.infrastructure.provisioning.script_manifest import (
    DEDICATED_RUNTIME_REQUIRED_TABLES,
    load_dedicated_schema_manifest,
)


def _db_name() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    suffix = uuid.uuid4().hex[:6]
    return f"erp_f12g3_{stamp}_{suffix}"


async def _table_exists(ddl, database: str, table: str) -> bool:
    escaped = table.replace("'", "''")
    val = await ddl.scalar_int(
        f"SELECT CASE WHEN OBJECT_ID(N'dbo.{escaped}', N'U') IS NOT NULL THEN 1 ELSE 0 END",
        database=database,
    )
    return bool(val)


async def main() -> int:
    if os.getenv("PROVISIONING_DDL_EXECUTOR_ENABLED", "").lower() != "true":
        print("SKIP: PROVISIONING_DDL_EXECUTOR_ENABLED != true")
        return 0

    ddl = create_default_ddl_client()
    db_name = _db_name()
    cliente_id = uuid.uuid4()
    manifest = load_dedicated_schema_manifest()

    print(f"F12-G3 validate — database={db_name} manifest={manifest.version}")

    await ddl.execute(f"CREATE DATABASE [{db_name}];", database="master")
    print("CREATE DATABASE ok")

    runner = BootstrapScriptRunner(ddl_client=ddl)
    request = BootstrapScriptRunRequest(
        database_name=db_name,
        cliente_id=cliente_id,
        profile=manifest.profile,
    )
    result = await runner.run_dedicated_schema_bootstrap(request)
    print(f"Bootstrap executed: {result.scripts_executed}")
    print(f"Bootstrap skipped: {result.scripts_skipped}")

    missing: list[str] = []
    for table in sorted(DEDICATED_RUNTIME_REQUIRED_TABLES):
        if not await _table_exists(ddl, db_name, table):
            missing.append(table)

    auth_audit = await _table_exists(ddl, db_name, "auth_audit_log")
    print(f"auth_audit_log exists: {auth_audit}")

    if missing:
        print(f"FAIL missing tables: {missing}")
        return 1

    forbidden = {"user_session", "token_family", "refresh_tokens"}
    for table in sorted(forbidden):
        exists = await _table_exists(ddl, db_name, table)
        print(f"{table} in DP (expected absent): {exists}")
        if exists:
            print(f"WARN unexpected session table in DP: {table}")

    print("PASS all DEDICATED_RUNTIME_REQUIRED_TABLES present")
    print(f"Scripts in manifest: {len(manifest.entries)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
