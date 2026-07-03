import asyncio
import json
from sqlalchemy import text
from app.infrastructure.database.connection_async import DatabaseConnection
from app.infrastructure.database.queries_async import execute_query


async def main():
    out = {}
    q = text(
        "SELECT subdominio, nombre_bd, cliente_id FROM cliente "
        "WHERE subdominio IN ('acme','acmec') AND es_activo=1"
    )
    rows = await execute_query(q, connection_type=DatabaseConnection.ADMIN, client_id=None)
    out["tenants"] = rows
    acmec = next((x for x in rows if x.get("subdominio") == "acmec"), None)
    if acmec:
        cid = str(acmec["cliente_id"])
        for label, sql in [
            (
                "admin_permiso_count",
                "SELECT COUNT(*) AS n FROM permiso WHERE es_activo=1 AND codigo LIKE 'admin.%'",
            ),
            (
                "admin_grants",
                "SELECT codigo FROM permiso WHERE es_activo=1 "
                "AND codigo IN ('admin.usuario.leer','admin.rol.leer')",
            ),
            (
                "sync_marker",
                "SELECT script_code, checksum_sha256 FROM bootstrap_applied "
                "WHERE script_code='permission_catalog_sync'",
            ),
            (
                "session_count",
                "SELECT COUNT(*) AS n FROM user_session WHERE revoked_at IS NULL",
            ),
        ]:
            try:
                r = await execute_query(
                    text(sql),
                    connection_type=DatabaseConnection.DEFAULT,
                    client_id=cid,
                )
                out[label] = r
            except Exception as exc:
                out[f"{label}_error"] = str(exc)[:200]
    qcp = text(
        "SELECT COUNT(*) AS n FROM permiso WHERE es_activo=1 AND codigo LIKE 'admin.%'"
    )
    out["cp_admin"] = await execute_query(
        qcp, connection_type=DatabaseConnection.ADMIN, client_id=None
    )
    try:
        out["cp_sessions"] = await execute_query(
            text("SELECT COUNT(*) AS n FROM user_session WHERE revoked_at IS NULL"),
            connection_type=DatabaseConnection.ADMIN,
            client_id=None,
        )
    except Exception as exc:
        out["cp_sessions_error"] = str(exc)[:150]
    print(json.dumps(out, default=str, indent=2))


asyncio.run(main())
