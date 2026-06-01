import asyncio
import json
from sqlalchemy import text
from app.infrastructure.database.connection_async import DatabaseConnection, get_db_connection

CID = "EB067FE5-92C5-449B-9845-F9FE36B28A40"


async def main():
    async with get_db_connection(DatabaseConnection.ADMIN) as s:
        row = (await s.execute(text("""
            SELECT c.subdominio, c.codigo_cliente,
              (SELECT COUNT(*) FROM cliente_modulo cm WHERE cm.cliente_id=c.cliente_id AND cm.esta_activo=1),
              (SELECT STRING_AGG(m.codigo, ',') WITHIN GROUP (ORDER BY m.codigo)
               FROM cliente_modulo cm JOIN modulo m ON m.modulo_id=cm.modulo_id
               WHERE cm.cliente_id=c.cliente_id AND cm.esta_activo=1),
              (SELECT COUNT(*) FROM rol_permiso rp
               JOIN rol r ON r.rol_id=rp.rol_id AND r.codigo_rol='ADMIN_TENANT'
               WHERE rp.cliente_id=c.cliente_id),
              (SELECT TOP 1 u.nombre_usuario FROM usuario u
               WHERE u.cliente_id=c.cliente_id AND u.es_activo=1 ORDER BY u.nombre_usuario)
            FROM cliente c WHERE c.cliente_id=:cid
        """), {"cid": CID})).fetchone()
        perms = (await s.execute(text("""
            SELECT p.codigo FROM rol_permiso rp
            JOIN rol r ON r.rol_id=rp.rol_id AND r.codigo_rol='ADMIN_TENANT'
            JOIN permiso p ON p.permiso_id=rp.permiso_id AND p.es_activo=1
            WHERE rp.cliente_id=:cid
            ORDER BY p.codigo
        """), {"cid": CID})).fetchall()
    sample = [
        "core.app.acceder", "org.empresa.crear", "org.empresa.leer",
        "modulos.menu.leer", "admin.usuario.leer", "tenant.cliente.crear",
    ]
    codes = [r[0] for r in perms]
    print(json.dumps({
        "subdominio": row[0],
        "codigo_cliente": row[1],
        "cliente_modulo_count": row[2],
        "modulos": row[3],
        "rol_permiso_admin_count": row[4],
        "admin_username": row[5],
        "total_perm_codes_admin": len(codes),
        "sample_checks": {c: c in codes for c in sample},
        "has_tenant_cliente_crear": "tenant.cliente.crear" in codes,
    }, indent=2))


asyncio.run(main())
