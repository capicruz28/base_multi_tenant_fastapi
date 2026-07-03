import asyncio
import json
from uuid import UUID

from sqlalchemy import text

from app.infrastructure.provisioning.provisioning_dedicated_session import (
    provisioning_dedicated_session,
)

DB = "erp_cli013"
ADMIN_USER = UUID("a7027d36-e889-43f1-b932-d6779a699f7e")
ACMEC = UUID("6061C95E-CB3F-4BFE-9BCE-7607DE70549E")


async def main():
    async with provisioning_dedicated_session(DB) as s:
        r = await s.execute(
            text(
                """
                SELECT DISTINCT p.codigo, p.modulo_id, rp.permiso_id
                FROM usuario_rol ur
                INNER JOIN rol_permiso rp ON rp.rol_id = ur.rol_id AND rp.cliente_id = ur.cliente_id
                INNER JOIN permiso p ON p.permiso_id = rp.permiso_id AND p.es_activo = 1
                WHERE ur.usuario_id = :usuario_id
                  AND ur.cliente_id = :cliente_id
                  AND ur.es_activo = 1
                  AND p.codigo LIKE 'admin.%'
                ORDER BY p.codigo
                """
            ),
            {"usuario_id": str(ADMIN_USER), "cliente_id": str(ACMEC)},
        )
        rows = [dict(x) for x in r.mappings().all()]
        print(json.dumps({"admin_join_count": len(rows), "rows": rows}, default=str, indent=2))


asyncio.run(main())
