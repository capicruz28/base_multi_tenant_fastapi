#!/usr/bin/env python3
"""
Reparación idempotente RBAC cliente plataforma (ADMIN_PLATFORM + SYS_ADMIN).

Uso:
  python scripts/repair_platform_rbac.py --dry-run
  python scripts/repair_platform_rbac.py --apply
  python scripts/repair_platform_rbac.py --audit-only
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict
from uuid import UUID

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text

from app.core.config import settings
from app.infrastructure.database.connection_async import DatabaseConnection, get_db_connection
from app.modules.tenant.application.services.platform_rbac_bootstrap_service import (
    ADMIN_PLATFORM_ACCESS,
    CORE_APP_ACCEDER,
    PLATFORM_ADMIN_ROL_CODIGO,
    PlatformRbacBootstrapService,
)


async def _audit_snapshot(session) -> Dict[str, Any]:
    cid = PlatformRbacBootstrapService.resolve_platform_cliente_id()
    rol_row = (
        await session.execute(
            text("""
                SELECT rol_id FROM rol
                WHERE cliente_id = :cid AND codigo_rol = :codigo AND es_activo = 1
            """).bindparams(cid=str(cid), codigo=PLATFORM_ADMIN_ROL_CODIGO)
        )
    ).first()
    admin_rol_id = str(rol_row[0]) if rol_row else None
    rp_count = 0
    if admin_rol_id:
        rp_count = int(
            (
                await session.execute(
                    text("""
                        SELECT COUNT(*) FROM rol_permiso
                        WHERE cliente_id = :cid AND rol_id = :rid
                    """).bindparams(cid=str(cid), rid=admin_rol_id)
                )
            ).scalar()
            or 0
        )
    cm_count = int(
        (
            await session.execute(
                text("SELECT COUNT(*) FROM cliente_modulo WHERE cliente_id = :cid").bindparams(
                    cid=str(cid)
                )
            )
        ).scalar()
        or 0
    )
    perm_platform = (
        await session.execute(
            text("SELECT es_activo FROM permiso WHERE codigo = :c").bindparams(
                c=ADMIN_PLATFORM_ACCESS
            )
        )
    ).first()
    has_core_rp = False
    if admin_rol_id:
        has_core_rp = (
            await session.execute(
                text("""
                    SELECT 1 FROM rol_permiso rp
                    INNER JOIN permiso p ON p.permiso_id = rp.permiso_id
                    WHERE rp.cliente_id = :cid AND rp.rol_id = :rid AND p.codigo = :core
                """).bindparams(
                    cid=str(cid), rid=admin_rol_id, core=CORE_APP_ACCEDER
                )
            )
        ).first() is not None
    return {
        "cliente_id": str(cid),
        "admin_platform_rol_id": admin_rol_id,
        "rol_permiso_admin_platform_count": rp_count,
        "cliente_modulo_count": cm_count,
        "admin_platform_access_es_activo": bool(perm_platform and perm_platform[0]),
        "has_core_app_acceder_in_rol_permiso": has_core_rp,
        "needs_repair": rp_count < 5 or cm_count == 0 or not (perm_platform and perm_platform[0]),
    }


async def _run(*, dry_run: bool) -> int:
    before = {}
    after = {}
    async with get_db_connection(DatabaseConnection.ADMIN) as session:
        before = await _audit_snapshot(session)
        if dry_run:
            payload = {"dry_run": True, "before": before, "would_apply": before.get("needs_repair")}
            print(json.dumps(payload, indent=2, ensure_ascii=False))
            return 0

        result = await PlatformRbacBootstrapService.bootstrap_platform_rbac(session)
        await session.commit()
        after = await _audit_snapshot(session)

    payload = {
        "dry_run": False,
        "before": before,
        "after": after,
        "bootstrap": result,
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if not after.get("needs_repair") else 1


async def _audit_only() -> int:
    async with get_db_connection(DatabaseConnection.ADMIN) as session:
        snap = await _audit_snapshot(session)
    print(json.dumps({"audit": snap}, indent=2, ensure_ascii=False))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Platform RBAC repair (ADMIN_PLATFORM)")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--audit-only", action="store_true")
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if args.audit_only:
        return asyncio.run(_audit_only())
    return asyncio.run(_run(dry_run=args.dry_run))


if __name__ == "__main__":
    raise SystemExit(main())
