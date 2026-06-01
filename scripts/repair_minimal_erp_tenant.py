#!/usr/bin/env python3
"""
Reparación ERP mínima: org_empresa + vínculo admin para tenants sin empresa.

Uso:
  python scripts/repair_minimal_erp_tenant.py --subdominio smokerc2af1c02b --apply
  python scripts/repair_minimal_erp_tenant.py --cliente-id <UUID> --apply
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from uuid import UUID

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text

from app.infrastructure.database.connection_async import DatabaseConnection, get_db_connection
from app.modules.tenant.application.services.minimal_erp_tenant_bootstrap_service import (
    ADMIN_USERNAME,
    MinimalErpTenantBootstrapService,
)
from app.modules.tenant.presentation.schemas import ClienteCreate


async def _resolve_cliente(session, *, subdominio: str | None, cliente_id: UUID | None) -> dict:
    if cliente_id:
        q = text(
            "SELECT cliente_id, subdominio, razon_social, nombre_comercial, ruc, contacto_email "
            "FROM cliente WHERE cliente_id = :id"
        ).bindparams(id=str(cliente_id))
    else:
        q = text(
            "SELECT cliente_id, subdominio, razon_social, nombre_comercial, ruc, contacto_email "
            "FROM cliente WHERE subdominio = :sub"
        ).bindparams(sub=subdominio)
    row = (await session.execute(q)).fetchone()
    if not row:
        raise ValueError("Cliente no encontrado")
    return {
        "cliente_id": UUID(str(row[0])),
        "subdominio": row[1],
        "razon_social": row[2],
        "nombre_comercial": row[3],
        "ruc": row[4],
        "contacto_email": row[5],
    }


async def _audit(session, cliente_id: UUID) -> dict:
    emp_count = int(
        (
            await session.execute(
                text(
                    "SELECT COUNT(*) FROM org_empresa WHERE cliente_id = :cid AND es_activo = 1"
                ).bindparams(cid=str(cliente_id))
            )
        ).scalar()
        or 0
    )
    admin = (
        await session.execute(
            text("""
                SELECT u.usuario_id, u.empresa_default_id, ur.empresa_id, ur.es_empresa_default
                FROM usuario u
                LEFT JOIN usuario_rol ur ON ur.usuario_id = u.usuario_id AND ur.cliente_id = u.cliente_id
                LEFT JOIN rol r ON r.rol_id = ur.rol_id AND r.codigo_rol = 'ADMIN_TENANT'
                WHERE u.cliente_id = :cid AND u.nombre_usuario = :user AND u.es_eliminado = 0
            """).bindparams(cid=str(cliente_id), user=ADMIN_USERNAME)
        )
    ).first()
    return {
        "org_empresa_count": emp_count,
        "admin_usuario_id": str(admin[0]) if admin else None,
        "empresa_default_id": str(admin[1]) if admin and admin[1] else None,
        "usuario_rol_empresa_id": str(admin[2]) if admin and admin[2] else None,
        "admin_tenant_wide": admin[2] is None if admin else False,
        "es_empresa_default": bool(admin[3]) if admin and admin[3] is not None else False,
        "needs_repair": emp_count == 0
        or (admin and admin[1] is None)
        or (admin and admin[2] is not None),
    }


async def _run(*, subdominio: str | None, cliente_id: UUID | None, apply: bool) -> int:
    async with get_db_connection(DatabaseConnection.ADMIN) as session:
        cli = await _resolve_cliente(session, subdominio=subdominio, cliente_id=cliente_id)
        cid = cli["cliente_id"]
        before = await _audit(session, cid)
        if not apply:
            print(json.dumps({"dry_run": True, "cliente": cli, "before": before}, indent=2))
            return 0

        cliente_data = ClienteCreate(
            codigo_cliente="REPAIR",
            subdominio=cli["subdominio"],
            razon_social=cli["razon_social"] or "Empresa Reparada",
            nombre_comercial=cli.get("nombre_comercial"),
            ruc=cli.get("ruc"),
            contacto_email=cli["contacto_email"] or "admin@repair.local",
        )
        admin_row = (
            await session.execute(
                text("""
                    SELECT u.usuario_id, r.rol_id
                    FROM usuario u
                    INNER JOIN usuario_rol ur ON ur.usuario_id = u.usuario_id
                    INNER JOIN rol r ON r.rol_id = ur.rol_id
                    WHERE u.cliente_id = :cid AND u.nombre_usuario = :user
                      AND r.codigo_rol = 'ADMIN_TENANT'
                """).bindparams(cid=str(cid), user=ADMIN_USERNAME)
            )
        ).first()
        if not admin_row:
            raise ValueError("Usuario admin / rol ADMIN_TENANT no encontrado")

        result = await MinimalErpTenantBootstrapService.bootstrap_minimal_erp(
            session,
            cliente_id=cid,
            cliente_data=cliente_data,
            usuario_id=UUID(str(admin_row[0])),
            admin_rol_id=UUID(str(admin_row[1])),
        )
        await session.commit()
        after = await _audit(session, cid)

    print(
        json.dumps(
            {"cliente": cli, "before": before, "after": after, "bootstrap": result},
            indent=2,
            ensure_ascii=False,
            default=str,
        )
    )
    return 0 if not after.get("needs_repair") else 1


def main() -> int:
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--subdominio")
    g.add_argument("--cliente-id")
    p.add_argument("--apply", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    cid = UUID(args.cliente_id) if args.cliente_id else None
    return asyncio.run(
        _run(subdominio=args.subdominio, cliente_id=cid, apply=args.apply and not args.dry_run)
    )


if __name__ == "__main__":
    raise SystemExit(main())
