#!/usr/bin/env python3
"""
Reparación idempotente RBAC/módulos base en tenants legacy (runtime bootstrap).

Equivalente operativo a R010+R020 sin ejecutar SQL legacy.

Uso:
  # Solo auditoría (reporte antes)
  python scripts/repair_legacy_tenant_rbac.py --audit-only

  # Simulación (sin commit)
  python scripts/repair_legacy_tenant_rbac.py --dry-run

  # Aplicar reparación
  python scripts/repair_legacy_tenant_rbac.py --apply

  # Un tenant
  python scripts/repair_legacy_tenant_rbac.py --dry-run --cliente-id <UUID>

Salida: JSON en stdout (before/after por tenant reparado).
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from uuid import UUID

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import importlib.util

from app.infrastructure.database.connection_async import DatabaseConnection, get_db_connection

_repair_path = PROJECT_ROOT / "app/modules/tenant/application/services/legacy_tenant_rbac_repair_service.py"
_mod_name = "legacy_tenant_rbac_repair_service"
_spec = importlib.util.spec_from_file_location(_mod_name, _repair_path)
_repair_mod = importlib.util.module_from_spec(_spec)
sys.modules[_mod_name] = _repair_mod
assert _spec.loader is not None
_spec.loader.exec_module(_repair_mod)

LegacyTenantRbacRepairService = _repair_mod.LegacyTenantRbacRepairService
report_to_json = _repair_mod.report_to_json


def _parse_cliente_ids(raw: list[str] | None) -> list[UUID] | None:
    if not raw:
        return None
    return [UUID(x) for x in raw]


async def _audit_only(cliente_ids: list[UUID] | None) -> int:
    async with get_db_connection(DatabaseConnection.ADMIN) as session:
        snapshots = await LegacyTenantRbacRepairService.audit_tenants(
            session, cliente_ids=cliente_ids
        )
    payload = {
        "mode": "audit_only",
        "audited_total": len(snapshots),
        "repair_candidates": sum(1 for s in snapshots if s.needs_repair and not s.skipped),
        "tenants": [s.to_dict() for s in snapshots],
    }
    import json

    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


async def _run(dry_run: bool, cliente_ids: list[UUID] | None) -> int:
    report = await LegacyTenantRbacRepairService.run_batch(
        dry_run=dry_run,
        cliente_ids=cliente_ids,
        only_candidates=True,
    )
    print(report_to_json(report))
    failed = sum(1 for o in report.outcomes if o.status == "failed")
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Legacy tenant RBAC repair (idempotent)")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--audit-only", action="store_true", help="Solo detectar y reportar")
    mode.add_argument("--dry-run", action="store_true", help="Simular reparación (sin commit)")
    mode.add_argument("--apply", action="store_true", help="Aplicar reparación (commit por tenant)")
    parser.add_argument(
        "--cliente-id",
        action="append",
        dest="cliente_ids",
        help="Limitar a uno o más cliente_id (UUID). Repetible.",
    )
    args = parser.parse_args()
    cliente_ids = _parse_cliente_ids(args.cliente_ids)

    if args.audit_only:
        return asyncio.run(_audit_only(cliente_ids))
    if args.dry_run:
        return asyncio.run(_run(dry_run=True, cliente_ids=cliente_ids))
    return asyncio.run(_run(dry_run=False, cliente_ids=cliente_ids))


if __name__ == "__main__":
    raise SystemExit(main())
