"""RC-03A audit SQL — read-only."""
import asyncio
import json

from sqlalchemy import text

from app.infrastructure.database.connection_async import DatabaseConnection
from app.infrastructure.database.queries_async import execute_query
from app.infrastructure.provisioning.provisioning_dedicated_session import (
    provisioning_dedicated_session,
)

ACMEC = "6061C95E-CB3F-4BFE-9BCE-7607DE70549E"
DB = "erp_cli013"


async def q_admin(sql: str):
    return await execute_query(text(sql), connection_type=DatabaseConnection.ADMIN, client_id=None)


async def main():
    out = {}

    try:
        out["provisioning_runs"] = await q_admin(
            f"SELECT TOP 3 provisioning_run_id, provisioning_state, started_at, ready_at, failed_at "
            f"FROM tenant_provisioning_run WHERE cliente_id = '{ACMEC}' ORDER BY started_at DESC"
        )
        if out["provisioning_runs"]:
            run_id = out["provisioning_runs"][0]["provisioning_run_id"]
            out["provisioning_steps"] = await q_admin(
                f"SELECT step_code, step_status, saga_order, started_at, completed_at "
                f"FROM tenant_provisioning_step WHERE provisioning_run_id = '{run_id}' ORDER BY saga_order"
            )
    except Exception as exc:
        out["provisioning_error"] = str(exc)[:300]

    async with provisioning_dedicated_session(DB) as session:

        async def fetch(label: str, sql: str):
            try:
                r = await session.execute(text(sql))
                out[label] = [dict(row) for row in r.mappings().all()]
            except Exception as exc:
                out[label + "_error"] = str(exc)[:300]

        await fetch(
            "bootstrap_applied",
            "SELECT script_code, step_code, LEFT(checksum_sha256,24) AS hash_prefix, script_path "
            "FROM bootstrap_applied ORDER BY script_code",
        )
        await fetch(
            "admin_permiso",
            "SELECT codigo, modulo_id, es_activo, fecha_creacion, fecha_actualizacion "
            "FROM permiso WHERE codigo LIKE 'admin.%' ORDER BY codigo",
        )
        await fetch(
            "admin_rol_permiso",
            """
            SELECT p.codigo, p.modulo_id, rp.fecha_creacion
            FROM rol_permiso rp
            JOIN permiso p ON p.permiso_id = rp.permiso_id
            JOIN rol r ON r.rol_id = rp.rol_id
            WHERE r.codigo_rol = 'ADMIN_TENANT'
              AND p.codigo LIKE 'admin.%'
            ORDER BY p.codigo
            """,
        )
        await fetch(
            "permiso_totals",
            "SELECT COUNT(*) AS total, "
            "SUM(CASE WHEN codigo LIKE 'admin.%' THEN 1 ELSE 0 END) AS admin_count "
            "FROM permiso WHERE es_activo=1",
        )

    print(json.dumps(out, default=str, indent=2))


asyncio.run(main())
