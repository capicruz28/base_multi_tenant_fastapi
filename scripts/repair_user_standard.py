#!/usr/bin/env python3
"""
T3 — Aplicar bundle USER_STANDARD a USER_TENANT.

Idempotente.

Uso:
  python scripts/repair_user_standard.py --dry-run --all
  python scripts/repair_user_standard.py --subdominio prueba --apply
  python scripts/repair_user_standard.py --cliente-id <UUID> --apply
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
from app.modules.tenant.application.services.user_standard_constants import (
    USER_STANDARD_MENU_GRANTS,
    USER_STANDARD_PERMISSION_CODIGOS,
)
from app.modules.tenant.application.services.user_standard_service import UserStandardService


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


async def _list_tenant_ids(
    session, *, all_tenants: bool, cliente_id: Optional[UUID]
) -> List[UUID]:
    if not all_tenants:
        assert cliente_id is not None
        return [cliente_id]
    rows = (
        await session.execute(
            text(
                """
                SELECT DISTINCT c.cliente_id
                FROM cliente c
                INNER JOIN rol r ON r.cliente_id = c.cliente_id
                WHERE c.es_activo = 1
                  AND r.codigo_rol = 'USER_TENANT'
                  AND r.es_activo = 1
                ORDER BY c.cliente_id
                """
            )
        )
    ).fetchall()
    return [UUID(str(r[0])) for r in rows]


async def _audit_one(session, *, cliente_id: UUID) -> Dict[str, Any]:
    rid = await UserStandardService.resolve_user_rol_id(session, cliente_id=cliente_id)
    if not rid:
        return {
            "cliente_id": str(cliente_id),
            "rol_id": None,
            "codigo_rol": "USER_TENANT",
            "needs_repair": True,
            "reason": "USER_ROLE_NOT_FOUND",
        }

    ph = ", ".join(f":pc{i}" for i in range(len(USER_STANDARD_PERMISSION_CODIGOS)))
    bind = {f"pc{i}": USER_STANDARD_PERMISSION_CODIGOS[i] for i in range(len(USER_STANDARD_PERMISSION_CODIGOS))}
    sql_rp = text(
        f"""
        SELECT COUNT(DISTINCT p.codigo) AS c
        FROM rol_permiso rp
        INNER JOIN permiso p ON p.permiso_id = rp.permiso_id AND p.es_activo = 1
        WHERE rp.cliente_id = :cliente_id
          AND rp.rol_id = :rol_id
          AND p.codigo IN ({ph})
        """
    ).bindparams(**bind, cliente_id=cliente_id, rol_id=rid)
    rp_count = int(((await session.execute(sql_rp)).fetchone() or [0])[0])

    sql_rmp = text(
        """
        SELECT COUNT(*) AS c
        FROM rol_menu_permiso
        WHERE cliente_id = :cliente_id
          AND rol_id = :rol_id
          AND puede_ver = 1
        """
    ).bindparams(cliente_id=cliente_id, rol_id=rid)
    rmp_count = int(((await session.execute(sql_rmp)).fetchone() or [0])[0])

    expected_rp = len(USER_STANDARD_PERMISSION_CODIGOS)
    expected_rmp = len(USER_STANDARD_MENU_GRANTS)
    needs = rp_count < expected_rp or rmp_count < expected_rmp
    return {
        "cliente_id": str(cliente_id),
        "rol_id": str(rid),
        "rp_count": rp_count,
        "rp_expected": expected_rp,
        "rmp_ver_count": rmp_count,
        "rmp_expected": expected_rmp,
        "needs_repair": needs,
    }


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

        audits = []
        for cid in tenant_ids:
            audits.append(await _audit_one(session, cliente_id=cid))
        needs_before = [a for a in audits if a.get("needs_repair")]

        report: Dict[str, Any] = {
            "phase": "T3_USER_STANDARD",
            "mode": "apply" if apply else "dry_run",
            "scope": "all" if all_tenants else str(target_cid),
            "expected_permiso_codigos": list(USER_STANDARD_PERMISSION_CODIGOS),
            "expected_rmp_count": len(USER_STANDARD_MENU_GRANTS),
            "tenants_scanned": len(tenant_ids),
            "tenants_needing_repair_before": len(needs_before),
            "tenants_before": needs_before,
            "tenants": [],
            "total_rp_inserted": 0,
            "total_rmp_inserted": 0,
        }

        if apply:
            for cid in tenant_ids:
                rid = await UserStandardService.resolve_user_rol_id(
                    session, cliente_id=cid
                )
                if not rid:
                    continue
                one = await UserStandardService.apply_to_user_role(
                    session, cliente_id=cid, user_rol_id=rid
                )
                report["tenants"].append(one)
                report["total_rp_inserted"] += int(
                    (one.get("rol_permiso") or {}).get("inserted", 0) or 0
                )
                report["total_rmp_inserted"] += int(
                    (one.get("rol_menu_permiso") or {}).get("inserted", 0) or 0
                )
            await session.commit()

            audits_after = []
            for cid in tenant_ids:
                audits_after.append(await _audit_one(session, cliente_id=cid))
            needs_after = [a for a in audits_after if a.get("needs_repair")]
            report["tenants_needing_repair_after"] = len(needs_after)
            report["tenants_after"] = needs_after
        else:
            report["tenants_needing_repair_after"] = len(needs_before)

        report["passed"] = report.get("tenants_needing_repair_after", 0) == 0
        return report


def main() -> int:
    parser = argparse.ArgumentParser(description="T3 USER_STANDARD repair")
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

