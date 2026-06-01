#!/usr/bin/env python3
"""
T1 — Aplicar bundle BASE_OPERATIVE a MANAGER_TENANT y USER_TENANT.

Idempotente. No modifica ADMIN_TENANT (OWNER_FULL).

Uso:
  python scripts/repair_base_operative.py --dry-run --all
  python scripts/repair_base_operative.py --subdominio prueba --apply
  python scripts/repair_base_operative.py --cliente-id <UUID> --apply
  python scripts/repair_base_operative.py --all --apply \\
    --output app/bootstrap_v2/00_manifest/evidence/T1_BASE_OPERATIVE_REPAIR.json
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text

from app.infrastructure.database.connection_async import DatabaseConnection, get_db_connection
from app.modules.tenant.application.services.base_operative_constants import (
    BASE_OPERATIVE_PERMISSION_CODIGOS,
)
from app.modules.tenant.application.services.base_operative_service import BaseOperativeService


async def _resolve_cliente_id(session, *, subdominio: Optional[str]) -> UUID:
    row = (
        await session.execute(
            text("SELECT cliente_id FROM cliente WHERE subdominio = :sub").bindparams(
                sub=subdominio
            )
        )
    ).first()
    if not row:
        raise ValueError(f"Cliente no encontrado: subdominio={subdominio}")
    return UUID(str(row[0]))


async def _list_tenant_ids(session, *, all_tenants: bool, cliente_id: Optional[UUID]) -> List[UUID]:
    if not all_tenants:
        assert cliente_id is not None
        return [cliente_id]
    rows = (
        await session.execute(
            text("""
                SELECT DISTINCT c.cliente_id
                FROM cliente c
                INNER JOIN rol r ON r.cliente_id = c.cliente_id
                WHERE c.es_activo = 1
                  AND r.codigo_rol IN ('MANAGER_TENANT', 'USER_TENANT')
                  AND r.es_activo = 1
                ORDER BY c.cliente_id
            """)
        )
    ).fetchall()
    return [UUID(str(r[0])) for r in rows]


async def _run(
    *,
    subdominio: Optional[str],
    cliente_id: Optional[UUID],
    all_tenants: bool,
    apply: bool,
) -> Dict[str, Any]:
    if sum(bool(x) for x in (subdominio, cliente_id, all_tenants)) != 1:
        raise ValueError("Indique exactamente uno de: --subdominio, --cliente-id, --all")

    async with get_db_connection(DatabaseConnection.ADMIN) as session:
        target_cid: Optional[UUID] = cliente_id
        if subdominio:
            target_cid = await _resolve_cliente_id(session, subdominio=subdominio)

        tenant_ids = await _list_tenant_ids(
            session, all_tenants=all_tenants, cliente_id=target_cid
        )
        needs_repair_before = await BaseOperativeService.audit_operative_roles(
            session, cliente_id=None if all_tenants else target_cid
        )

        report: Dict[str, Any] = {
            "phase": "T1_BASE_OPERATIVE",
            "mode": "apply" if apply else "dry_run",
            "scope": "all" if all_tenants else str(target_cid),
            "expected_codigos": list(BASE_OPERATIVE_PERMISSION_CODIGOS),
            "tenants_scanned": len(tenant_ids),
            "roles_needing_repair_before": len(needs_repair_before),
            "incomplete_roles_before": needs_repair_before,
            "tenants": [],
            "total_inserted": 0,
        }

        if apply:
            for cid in tenant_ids:
                one = await BaseOperativeService.apply_to_operative_roles(
                    session, cliente_id=cid
                )
                report["tenants"].append(one)
                report["total_inserted"] += int(one.get("total_inserted", 0))
            await session.commit()
            for cid in tenant_ids:
                BaseOperativeService._invalidate_tenant_cache(cid)
            needs_after = await BaseOperativeService.audit_operative_roles(
                session, cliente_id=None if all_tenants else target_cid
            )
            report["roles_needing_repair_after"] = len(needs_after)
            report["incomplete_roles_after"] = needs_after
        else:
            report["roles_needing_repair_after"] = len(needs_repair_before)

        report["passed"] = report.get("roles_needing_repair_after", len(needs_repair_before)) == 0
        return report


def main() -> int:
    parser = argparse.ArgumentParser(description="T1 BASE_OPERATIVE repair")
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument("--subdominio")
    scope.add_argument("--cliente-id")
    scope.add_argument("--all", action="store_true")
    parser.add_argument("--apply", action="store_true", help="Ejecutar INSERT (default: dry-run)")
    parser.add_argument("--dry-run", action="store_true", help="Alias explícito de dry-run")
    parser.add_argument("--output", type=Path, help="Ruta JSON evidencia")
    args = parser.parse_args()

    apply = args.apply and not args.dry_run
    cliente_uuid = UUID(args.cliente_id) if args.cliente_id else None
    try:
        report = asyncio.run(
            _run(
                subdominio=args.subdominio,
                cliente_id=cliente_uuid,
                all_tenants=args.all,
                apply=apply,
            )
        )
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}, indent=2, ensure_ascii=False), file=sys.stderr)
        return 2

    payload = json.dumps(report, indent=2, ensure_ascii=False)
    print(payload)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")

    if apply and not report.get("passed", False):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
