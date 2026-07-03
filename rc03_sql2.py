import asyncio
import json
from sqlalchemy import text
from app.infrastructure.database.connection_async import DatabaseConnection
from app.infrastructure.database.queries_async import execute_query


async def main():
    out = {}
    q = text(
        "SELECT subdominio, cliente_id FROM cliente "
        "WHERE subdominio IN ('acme','acmec') AND es_activo=1"
    )
    rows = await execute_query(q, connection_type=DatabaseConnection.ADMIN, client_id=None)
    out["tenants"] = rows
    acmec = next((x for x in rows if x.get("subdominio") == "acmec"), None)
    acme = next((x for x in rows if x.get("subdominio") == "acme"), None)
    if acmec:
        cid = str(acmec["cliente_id"])
        for label, sql in [
            (
                "dp_admin_permiso_count",
                "SELECT COUNT(*) AS n FROM permiso WHERE es_activo=1 AND codigo LIKE 'admin.%'",
            ),
            (
                "dp_admin_grants",
                "SELECT codigo FROM permiso WHERE es_activo=1 "
                "AND codigo IN ('admin.usuario.leer','admin.rol.leer')",
            ),
            (
                "dp_sync_marker",
                "SELECT script_code, LEFT(checksum_sha256,20) AS hash_prefix "
                "FROM bootstrap_applied WHERE script_code='permission_catalog_sync'",
            ),
            (
                "dp_sessions",
                "SELECT COUNT(*) AS n FROM user_session WHERE revoked_at IS NULL",
            ),
            (
                "dp_total_permiso",
                "SELECT COUNT(*) AS n FROM permiso WHERE es_activo=1",
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
                out[f"{label}_error"] = str(exc)[:220]
    if acme:
        cid = str(acme["cliente_id"])
        try:
            out["shared_admin_grants"] = await execute_query(
                text(
                    "SELECT codigo FROM permiso WHERE es_activo=1 "
                    "AND codigo IN ('admin.usuario.leer','admin.rol.leer')"
                ),
                connection_type=DatabaseConnection.DEFAULT,
                client_id=cid,
            )
        except Exception as exc:
            out["shared_admin_grants_error"] = str(exc)[:220]
    out["cp_admin"] = await execute_query(
        text("SELECT COUNT(*) AS n FROM permiso WHERE es_activo=1 AND codigo LIKE 'admin.%'"),
        connection_type=DatabaseConnection.ADMIN,
        client_id=None,
    )
    try:
        out["cp_sessions"] = await execute_query(
            text("SELECT COUNT(*) AS n FROM user_session WHERE revoked_at IS NULL"),
            connection_type=DatabaseConnection.ADMIN,
            client_id=None,
        )
    except Exception as exc:
        out["cp_sessions_error"] = str(exc)[:180]
    print(json.dumps(out, default=str, indent=2))


asyncio.run(main())
