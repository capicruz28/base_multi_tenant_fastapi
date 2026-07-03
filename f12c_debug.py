import asyncio
import json

from sqlalchemy import text

from app.infrastructure.provisioning.provisioning_dedicated_session import (
    provisioning_dedicated_session,
)
from app.modules.rbac.application.services.permisos_usuario_service import (
    obtener_codigos_permiso_usuario,
)

DB = "erp_cli013"
ACMEC = "6061C95E-CB3F-4BFE-9BCE-7607DE70549E"
ADMIN_USER = "a7027d36-e889-43f1-b932-d6779a699f7e"


async def main():
    out = {}
    async with provisioning_dedicated_session(DB) as s:

        async def f(q, params=None):
            r = await s.execute(text(q), params or {})
            return [dict(x) for x in r.mappings().all()]

        out["admin_modulo_id"] = await f(
            "SELECT codigo, modulo_id FROM permiso "
            "WHERE codigo IN ('admin.usuario.leer','admin.rol.leer')"
        )
        out["usuario_rol"] = await f(
            """
            SELECT u.nombre_usuario, r.codigo_rol, ur.empresa_id, ur.es_activo
            FROM usuario u
            JOIN usuario_rol ur ON ur.usuario_id = u.usuario_id AND ur.cliente_id = u.cliente_id
            JOIN rol r ON r.rol_id = ur.rol_id
            WHERE u.nombre_usuario = 'admin' AND ur.es_activo = 1
            """
        )
        out["cliente_modulo_count"] = await f(
            "SELECT COUNT(*) AS n FROM cliente_modulo WHERE esta_activo = 1"
        )

    codes = await obtener_codigos_permiso_usuario(
        usuario_id=ADMIN_USER,
        cliente_id=ACMEC,
        database_type="multi",
        filter_by_active_modules=True,
    )
    out["resolver_codes_count"] = len(codes)
    out["has_admin_usuario_leer"] = "admin.usuario.leer" in codes
    out["has_admin_rol_leer"] = "admin.rol.leer" in codes
    out["admin_codes_in_resolver"] = sorted(c for c in codes if c.startswith("admin."))
    print(json.dumps(out, default=str, indent=2))


asyncio.run(main())
