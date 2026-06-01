#!/usr/bin/env python3
"""
M4 — Promover ADMIN_TENANT scoped → tenant-wide (usuario_rol.empresa_id = NULL).

Idempotente. Solo afecta filas activas con rol codigo_rol = 'ADMIN_TENANT'.
No modifica MANAGER_TENANT ni USER_TENANT.

Uso:
  python scripts/repair_admin_tenant_tenant_wide.py --dry-run
  python scripts/repair_admin_tenant_tenant_wide.py --subdominio prueba --apply
  python scripts/repair_admin_tenant_tenant_wide.py --cliente-id <UUID> --apply
  python scripts/repair_admin_tenant_tenant_wide.py --all --apply
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

ADMIN_CODIGO = "C70B1037-EFC2-49F2-B755-464AD3D5A57B"


async def _list_scoped_admin_assignments(
    session,
    *,
    cliente_id: Optional[UUID] = None,
) -> List[Dict[str, Any]]:
    cid_filter = "AND ur.cliente_id = :cliente_id" if cliente_id else ""
    bind = {"codigo": ADMIN_CODIGO}
    if cliente_id:
        bind["cliente_id"] = str(cliente_id)

    result = await session.execute(
        text(f"""
            SELECT
                ur.usuario_rol_id,
                ur.usuario_id,
                ur.cliente_id,
                ur.empresa_id,
                u.nombre_usuario,
                c.subdominio
            FROM usuario_rol ur
            INNER JOIN rol r ON r.rol_id = ur.rol_id
            INNER JOIN usuario u ON u.usuario_id = ur.usuario_id
                AND u.cliente_id = ur.cliente_id AND u.es_eliminado = 0
            INNER JOIN cliente c ON c.cliente_id = ur.cliente_id
            WHERE r.rol_id = :codigo
              AND ur.es_activo = 1
              AND ur.empresa_id IS NOT NULL
              {cid_filter}
            ORDER BY c.subdominio, u.nombre_usuario
        """).bindparams(**bind)
    )
    rows = result.fetchall()
    out: List[Dict[str, Any]] = []
    for row in rows:
        out.append(
            {
                "usuario_rol_id": str(row[0]),
                "usuario_id": str(row[1]),
                "cliente_id": str(row[2]),
                "empresa_id_scoped": str(row[3]),
                "nombre_usuario": row[4],
                "subdominio": row[5],
            }
        )
    return out


async def _apply_promotion(session, assignments: List[Dict[str, Any]]) -> int:
    updated = 0
    for item in assignments:
        result = await session.execute(
            text("""
                UPDATE usuario_rol
                SET empresa_id = NULL
                WHERE usuario_rol_id = :ur_id
                  AND es_activo = 1
            """).bindparams(ur_id=item["usuario_rol_id"])
        )
        updated += int(getattr(result, "rowcount", 0) or 0)
    return updated


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
            row = (
                await session.execute(
                    text(
                        "SELECT cliente_id FROM cliente WHERE subdominio = :sub"
                    ).bindparams(sub=subdominio)
                )
            ).first()
            if not row:
                raise ValueError(f"Cliente no encontrado: subdominio={subdominio}")
            target_cid = UUID(str(row[0]))

        scoped = await _list_scoped_admin_assignments(
            session, cliente_id=None if all_tenants else target_cid
        )
        report: Dict[str, Any] = {
            "phase": "M4",
            "mode": "apply" if apply else "dry_run",
            "scope": "all" if all_tenants else str(target_cid),
            "scoped_admin_count": len(scoped),
            "assignments": scoped,
            "updated": 0,
        }

        if apply and scoped:
            report["updated"] = await _apply_promotion(session, scoped)
            await session.commit()
            scoped_after = await _list_scoped_admin_assignments(
                session, cliente_id=None if all_tenants else target_cid
            )
            report["scoped_admin_remaining"] = len(scoped_after)
        elif not apply:
            report["scoped_admin_remaining"] = len(scoped)

        return report


def main() -> int:
    parser = argparse.ArgumentParser(description="M4 ADMIN_TENANT tenant-wide repair")
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument("--subdominio")
    scope.add_argument("--cliente-id")
    scope.add_argument("--all", action="store_true")
    parser.add_argument("--apply", action="store_true", help="Ejecutar UPDATE (default: dry-run)")
    parser.add_argument(
        "--output",
        type=Path,
        help="Ruta JSON evidencia (default: stdout only)",
    )
    args = parser.parse_args()

    cliente_uuid = UUID(args.cliente_id) if args.cliente_id else None
    try:
        report = asyncio.run(
            _run(
                subdominio=args.subdominio,
                cliente_id=cliente_uuid,
                all_tenants=args.all,
                apply=args.apply,
            )
        )
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}, indent=2), file=sys.stderr)
        return 2

    payload = json.dumps(report, indent=2, ensure_ascii=False)
    print(payload)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")

    if report.get("scoped_admin_remaining", report["scoped_admin_count"]) > 0 and args.apply:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
