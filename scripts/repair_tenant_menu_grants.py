#!/usr/bin/env python3
"""
Reparación rol_menu_permiso (sidebar UI) para tenants con ORG/SYS_ADMIN sin grants de menú.

Uso:
  python scripts/repair_tenant_menu_grants.py --dry-run
  python scripts/repair_tenant_menu_grants.py --apply
  python scripts/repair_tenant_menu_grants.py --subdominio smokerc69929718 --dry-run
  python scripts/repair_tenant_menu_grants.py --cliente-id <UUID> --apply
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text

from app.infrastructure.database.connection_async import DatabaseConnection, get_db_connection
from app.modules.tenant.application.services.minimal_erp_tenant_bootstrap_service import (
    ADMIN_USERNAME,
)
from app.modules.tenant.application.services.onboarding_menu_bootstrap_service import (
    ADMIN_ROL_CODIGO,
    MIN_HEALTHY_TENANT_ADMIN_MENU_GRANTS,
    OnboardingMenuBootstrapService,
)

EVIDENCE_DIR = PROJECT_ROOT / "app/bootstrap_v2/00_manifest/evidence"
MIN_RMP_HEALTHY = MIN_HEALTHY_TENANT_ADMIN_MENU_GRANTS


async def _resolve_cliente(session, *, subdominio: str | None, cliente_id: UUID | None) -> dict:
    if cliente_id:
        q = text(
            "SELECT cliente_id, subdominio, razon_social FROM cliente WHERE cliente_id = :id"
        ).bindparams(id=str(cliente_id))
    else:
        q = text(
            "SELECT cliente_id, subdominio, razon_social FROM cliente WHERE subdominio = :sub"
        ).bindparams(sub=subdominio)
    row = (await session.execute(q)).fetchone()
    if not row:
        raise ValueError("Cliente no encontrado")
    return {
        "cliente_id": UUID(str(row[0])),
        "subdominio": row[1],
        "razon_social": row[2],
    }


async def _expected_menu_targets(session, cliente_id: UUID) -> int:
    return await OnboardingMenuBootstrapService.count_expected_tenant_admin_menus(
        session, cliente_id=cliente_id
    )


async def _count_duplicates(session, cliente_id: UUID, admin_rol_id: UUID) -> int:
    row = (
        await session.execute(
            text("""
                SELECT COUNT(*) FROM (
                    SELECT menu_id
                    FROM rol_menu_permiso
                    WHERE cliente_id = :cid AND rol_id = :rid AND empresa_id IS NULL
                    GROUP BY menu_id
                    HAVING COUNT(*) > 1
                ) d
            """).bindparams(cid=str(cliente_id), rid=str(admin_rol_id))
        )
    ).fetchone()
    return int(row[0] if row else 0)


async def _audit(session, cliente_id: UUID, *, subdominio: str | None = None) -> dict:
    rmp = int(
        (
            await session.execute(
                text("""
                    SELECT COUNT(*)
                    FROM rol_menu_permiso rmp
                    INNER JOIN rol r ON r.rol_id = rmp.rol_id
                    WHERE rmp.cliente_id = :cid AND r.codigo_rol = :codigo
                """).bindparams(cid=str(cliente_id), codigo=ADMIN_ROL_CODIGO)
            )
        ).scalar()
        or 0
    )
    modulos = (
        await session.execute(
            text("""
                SELECT m.codigo
                FROM cliente_modulo cm
                INNER JOIN modulo m ON m.modulo_id = cm.modulo_id
                WHERE cm.cliente_id = :cid AND cm.esta_activo = 1
                  AND m.codigo IN ('ORG', 'SYS_ADMIN')
            """).bindparams(cid=str(cliente_id))
        )
    ).fetchall()
    admin_rol = (
        await session.execute(
            text("""
                SELECT rol_id FROM rol
                WHERE cliente_id = :cid AND codigo_rol = :codigo AND es_activo = 1
            """).bindparams(cid=str(cliente_id), codigo=ADMIN_ROL_CODIGO)
        )
    ).fetchone()
    expected = await _expected_menu_targets(session, cliente_id)
    admin_rol_id = UUID(str(admin_rol[0])) if admin_rol else None
    dupes = 0
    if admin_rol_id:
        dupes = await _count_duplicates(session, cliente_id, admin_rol_id)

    has_base_modulos = "ORG" in [str(r[0]) for r in modulos] and "SYS_ADMIN" in [
        str(r[0]) for r in modulos
    ]
    needs_repair = (
        has_base_modulos
        and bool(admin_rol_id)
        and expected > 0
        and (rmp < MIN_HEALTHY_TENANT_ADMIN_MENU_GRANTS or rmp != expected)
    )

    return {
        "cliente_id": str(cliente_id),
        "subdominio": subdominio,
        "rol_menu_permiso_admin": rmp,
        "expected_menu_grants": expected,
        "inserts_expected": max(0, expected - rmp) if rmp < expected else 0,
        "duplicate_menu_keys": dupes,
        "cliente_modulo_base": [str(r[0]) for r in modulos],
        "admin_rol_id": str(admin_rol_id) if admin_rol_id else None,
        "needs_repair": needs_repair,
        "skipped_reason": _skip_reason(has_base_modulos, admin_rol_id, expected, rmp),
    }


def _skip_reason(
    has_base_modulos: bool,
    admin_rol_id: Optional[UUID],
    expected: int,
    rmp: int,
) -> Optional[str]:
    if not admin_rol_id:
        return "no_admin_tenant_role"
    if not has_base_modulos:
        return "missing_org_or_sys_admin_module"
    if expected == 0:
        return "no_menu_catalog_targets"
    if rmp >= MIN_RMP_HEALTHY:
        return "already_healthy"
    return None


async def _list_tenant_rows(session, cliente_ids: Optional[List[UUID]] = None) -> List[dict]:
    if cliente_ids:
        placeholders = ", ".join(f":id{i}" for i in range(len(cliente_ids)))
        bind = {f"id{i}": str(cliente_ids[i]) for i in range(len(cliente_ids))}
        sql = text(f"""
            SELECT cliente_id, subdominio, razon_social
            FROM cliente
            WHERE es_activo = 1 AND cliente_id IN ({placeholders})
            ORDER BY subdominio
        """).bindparams(**bind)
    else:
        sql = text("""
            SELECT c.cliente_id, c.subdominio, c.razon_social
            FROM cliente c
            WHERE c.es_activo = 1
              AND EXISTS (
                    SELECT 1 FROM cliente_modulo cm
                    INNER JOIN modulo m ON m.modulo_id = cm.modulo_id
                    WHERE cm.cliente_id = c.cliente_id
                      AND cm.esta_activo = 1
                      AND m.codigo IN ('ORG', 'SYS_ADMIN')
              )
            ORDER BY c.subdominio
        """)
    rows = (await session.execute(sql)).fetchall()
    return [
        {
            "cliente_id": UUID(str(r[0])),
            "subdominio": r[1],
            "razon_social": r[2],
        }
        for r in rows
    ]


async def _repair_one(session, cliente_id: UUID, admin_rol_id: UUID) -> dict:
    before = await _audit(session, cliente_id)
    grants = await OnboardingMenuBootstrapService.bootstrap_admin_menu_grants(
        session,
        cliente_id=cliente_id,
        admin_rol_id=admin_rol_id,
    )
    after = await _audit(session, cliente_id)
    return {"before": before, "after": after, "grants": grants}


async def _run_batch(*, dry_run: bool, cliente_ids: Optional[List[UUID]] = None) -> dict:
    tenants_out: List[dict] = []
    repaired: List[str] = []
    omitted: List[dict] = []
    failed: List[dict] = []

    async with get_db_connection(DatabaseConnection.ADMIN) as session:
        rows = await _list_tenant_rows(session, cliente_ids)
        for row in rows:
            cid = row["cliente_id"]
            snap = await _audit(session, cid, subdominio=row.get("subdominio"))
            entry = {**row, "audit": snap}

            if not snap["needs_repair"]:
                omitted.append(
                    {
                        "subdominio": row["subdominio"],
                        "cliente_id": str(cid),
                        "reason": snap.get("skipped_reason"),
                        "rol_menu_permiso_admin": snap["rol_menu_permiso_admin"],
                    }
                )
                tenants_out.append(entry)
                continue

            if dry_run:
                entry["action"] = "would_repair"
                tenants_out.append(entry)
                continue

            try:
                outcome = await _repair_one(
                    session, cid, UUID(snap["admin_rol_id"])
                )
                await session.commit()
                entry["action"] = "repaired"
                entry["repair"] = outcome
                if outcome["after"]["rol_menu_permiso_admin"] >= MIN_RMP_HEALTHY:
                    repaired.append(row["subdominio"])
                else:
                    failed.append(
                        {
                            "subdominio": row["subdominio"],
                            "reason": "count_below_threshold_after_apply",
                        }
                    )
            except Exception as exc:
                await session.rollback()
                entry["action"] = "failed"
                entry["error"] = str(exc)
                failed.append({"subdominio": row["subdominio"], "error": str(exc)})
            tenants_out.append(entry)

    candidates = [t for t in tenants_out if t.get("audit", {}).get("needs_repair")]
    return {
        "mode": "dry_run" if dry_run else "apply",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "tenants_scanned": len(tenants_out),
        "repair_candidates": len(candidates),
        "repaired": repaired,
        "omitted": omitted,
        "failed": failed,
        "tenants": tenants_out,
    }


async def _run_single(
    *, subdominio: str | None, cliente_id: UUID | None, apply: bool
) -> int:
    async with get_db_connection(DatabaseConnection.ADMIN) as session:
        cli = await _resolve_cliente(session, subdominio=subdominio, cliente_id=cliente_id)
        cid = cli["cliente_id"]
        before = await _audit(session, cid, subdominio=cli["subdominio"])

        if not before.get("admin_rol_id"):
            print(
                json.dumps(
                    {
                        "error": f"Rol {ADMIN_ROL_CODIGO} no encontrado",
                        "cliente": cli,
                        "before": before,
                    },
                    indent=2,
                    default=str,
                )
            )
            return 2

        if not apply:
            print(
                json.dumps(
                    {"dry_run": True, "cliente": cli, "audit": before},
                    indent=2,
                    default=str,
                )
            )
            return 0

        if not before.get("needs_repair"):
            print(
                json.dumps(
                    {
                        "cliente": cli,
                        "audit": before,
                        "skipped": before.get("skipped_reason"),
                    },
                    indent=2,
                    default=str,
                )
            )
            return 0

        outcome = await _repair_one(session, cid, UUID(before["admin_rol_id"]))
        await session.commit()

    out = {
        "cliente": cli,
        "repair": outcome,
        "admin_username": ADMIN_USERNAME,
    }
    print(json.dumps(out, indent=2, ensure_ascii=False, default=str))
    return 0 if outcome["after"]["rol_menu_permiso_admin"] >= MIN_RMP_HEALTHY else 1


async def _validate_http_menu(
    *,
    base_url: str,
    subdominio: str,
    username: str = ADMIN_USERNAME,
    password: str,
) -> dict:
    from scripts.lib.http_smoke_runner import run_tenant_smoke

    report = run_tenant_smoke(
        base_url=base_url,
        subdominio=subdominio,
        username=username,
        password=password,
    )
    menu_step = next((s for s in report.steps if s.name == "auth_menu"), None)
    return {
        "smoke_passed": report.passed,
        "auth_menu": menu_step.detail if menu_step else None,
        "steps": [
            {"name": s.name, "ok": s.ok, "status": s.status}
            for s in report.steps
        ],
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Repair rol_menu_permiso for tenant sidebar")
    g = p.add_mutually_exclusive_group(required=False)
    g.add_argument("--subdominio")
    g.add_argument("--cliente-id")
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    p.add_argument(
        "--output",
        help="Ruta JSON de evidencia (batch). Default: evidence/MENU_GRANTS_REPAIR_<mode>.json",
    )
    p.add_argument(
        "--smoke-base-url",
        default="http://localhost:8000",
        help="Validación HTTP post-repair (solo tenants con credenciales en --credentials-json)",
    )
    p.add_argument(
        "--credentials-json",
        help="Mapa subdominio -> password para smoke post-repair",
    )
    args = p.parse_args()
    cid = UUID(args.cliente_id) if args.cliente_id else None
    cliente_ids = [cid] if cid else None

    if args.subdominio or args.cliente_id:
        return asyncio.run(
            _run_single(
                subdominio=args.subdominio,
                cliente_id=cid,
                apply=args.apply and not args.dry_run,
            )
        )

    async def _batch_with_evidence() -> int:
        payload = await _run_batch(
            dry_run=args.dry_run,
            cliente_ids=cliente_ids,
        )
        creds: Dict[str, str] = {}
        if args.credentials_json:
            creds = json.loads(Path(args.credentials_json).read_text(encoding="utf-8"))

        if args.apply and not args.dry_run and creds:
            payload["http_validation"] = []
            for sub in payload.get("repaired", []):
                pwd = creds.get(sub)
                if not pwd:
                    continue
                try:
                    http_val = await _validate_http_menu(
                        base_url=args.smoke_base_url,
                        subdominio=sub,
                        password=pwd,
                    )
                except Exception as exc:
                    http_val = {"smoke_passed": False, "error": str(exc)}
                payload["http_validation"].append(
                    {"subdominio": sub, **http_val}
                )

        out_path = args.output
        if not out_path:
            tag = "dry_run" if args.dry_run else "apply"
            out_path = str(EVIDENCE_DIR / f"MENU_GRANTS_REPAIR_{tag}.json")
        out_file = Path(out_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )
        print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))
        print(f"\nEvidencia: {out_file}", file=sys.stderr)
        return 1 if payload.get("failed") else 0

    return asyncio.run(_batch_with_evidence())


if __name__ == "__main__":
    raise SystemExit(main())
