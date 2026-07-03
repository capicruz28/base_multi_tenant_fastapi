import asyncio
import json
from sqlalchemy import text
from app.infrastructure.database.connection_async import DatabaseConnection
from app.infrastructure.database.queries_async import execute_query

ACMEC = "6061C95E-CB3F-4BFE-9BCE-7607DE70549E"


async def main():
    out = {}
    cid = ACMEC
    queries = {
        "rol_permiso_admin_usuario": """
            SELECT p.codigo FROM rol_permiso rp
            JOIN rol r ON r.rol_id = rp.rol_id
            JOIN permiso p ON p.permiso_id = rp.permiso_id
            WHERE r.codigo = 'ADMIN' AND p.codigo LIKE 'admin.usuario.%' AND rp.es_activo=1
        """,
        "rol_permiso_admin_rol": """
            SELECT p.codigo FROM rol_permiso rp
            JOIN rol r ON r.rol_id = rp.rol_id
            JOIN permiso p ON p.permiso_id = rp.permiso_id
            WHERE r.codigo = 'ADMIN' AND p.codigo LIKE 'admin.rol.%' AND rp.es_activo=1
        """,
        "admin_role_exists": "SELECT rol_id, codigo FROM rol WHERE codigo='ADMIN' AND es_activo=1",
    }
    for label, sql in queries.items():
        try:
            out[label] = await execute_query(
                text(sql), connection_type=DatabaseConnection.DEFAULT, client_id=cid
            )
        except Exception as exc:
            out[label + "_error"] = str(exc)[:200]

    q_alloc = text(
        "SELECT cc.nombre_bd FROM cliente_conexion cc "
        "JOIN cliente c ON c.cliente_id = cc.cliente_id "
        "WHERE c.subdominio='acmec' AND cc.es_activo=1"
    )
    try:
        out["acmec_db"] = await execute_query(
            q_alloc, connection_type=DatabaseConnection.ADMIN, client_id=None
        )
    except Exception as exc:
        out["acmec_db_error"] = str(exc)[:200]

    print(json.dumps(out, default=str, indent=2))


asyncio.run(main())
