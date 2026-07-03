import asyncio
import json
from uuid import UUID

from app.core.authorization.permission_resolver import get_permission_resolver
from app.core.tenant.context import TenantContext, set_tenant_context, reset_tenant_context

ACMEC = UUID("6061C95E-CB3F-4BFE-9BCE-7607DE70549E")
ADMIN = UUID("a7027d36-e889-43f1-b932-d6779a699f7e")
EMPRESA = UUID("782acdc9-235c-4faa-a982-61d3c2e74a55")


async def main():
    ctx = TenantContext(
        client_id=ACMEC,
        subdominio="acmec",
        database_type="multi",
        nombre_bd="erp_cli013",
    )
    tokens = set_tenant_context(ctx)
    try:
        resolver = get_permission_resolver()
        resolver.invalidate_for_tenant(ACMEC)
        eff = await resolver.get_effective_permissions(
            usuario_id=ADMIN,
            cliente_id=ACMEC,
            database_type="multi",
            empresa_id=EMPRESA,
        )
        codes = list(eff.codes)
        print(
            json.dumps(
                {
                    "count": len(codes),
                    "admin_usuario_leer": "admin.usuario.leer" in codes,
                    "admin_rol_leer": "admin.rol.leer" in codes,
                    "admin_codes": sorted(c for c in codes if c.startswith("admin.")),
                },
                indent=2,
            )
        )
    finally:
        reset_tenant_context(tokens)


asyncio.run(main())
