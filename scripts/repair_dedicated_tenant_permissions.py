#!/usr/bin/env python3
"""
F12-F — Utilidad oficial de reparación RBAC para tenants Dedicated existentes (solo desarrollo).

Replica el pipeline F12-C (acmec) de forma genérica:
  1. DedicatedPermissionCatalogSync
  2. bootstrap_global_grants_admin_tenant
  3. Invalidación de caches
  4. Reporte JSON

Uso:
  python scripts/repair_dedicated_tenant_permissions.py --subdominio acce --dry-run
  python scripts/repair_dedicated_tenant_permissions.py --subdominio acce --apply
  python scripts/repair_dedicated_tenant_permissions.py --cliente-id <UUID> --apply --validate-http
  python scripts/repair_dedicated_tenant_permissions.py --subdominio acce --apply \\
      --validate-http --password admin123 --base-url http://localhost:8000

Variables de entorno opcionales:
  SMOKE_BASE_URL, SMOKE_PASSWORD, SMOKE_FE_PORT
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from uuid import UUID

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.lib.dedicated_tenant_permission_repair import (  # noqa: E402
    DedicatedTenantPermissionRepairError,
    run_dedicated_permission_repair,
    validate_admin_api_http,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="F12-F — Repair catálogo permisos + grants globales (Dedicated, dev only)"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--cliente-id", dest="cliente_id", help="UUID del tenant")
    group.add_argument("--subdominio", help="Subdominio del tenant (ej. acce, acmec)")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Solo informa permisos/grants faltantes; no modifica datos",
    )
    mode.add_argument(
        "--apply",
        action="store_true",
        help="Ejecuta sync + grants + invalidación de cache",
    )
    parser.add_argument(
        "--validate-http",
        action="store_true",
        help="Tras --apply, valida GET permissions/me, usuarios/, roles/",
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("SMOKE_BASE_URL", "http://localhost:8000"),
    )
    parser.add_argument(
        "--password",
        default=os.environ.get("SMOKE_PASSWORD", "admin123"),
        help="Contraseña admin tenant para --validate-http",
    )
    parser.add_argument(
        "--username",
        default=os.environ.get("SMOKE_USERNAME", "admin"),
    )
    parser.add_argument(
        "--fe-port",
        default=os.environ.get("SMOKE_FE_PORT", "5173"),
    )
    return parser.parse_args()


async def _main() -> int:
    args = _parse_args()
    cliente_id = UUID(args.cliente_id) if args.cliente_id else None

    try:
        report = await run_dedicated_permission_repair(
            cliente_id=cliente_id,
            subdominio=args.subdominio,
            dry_run=args.dry_run,
        )
    except DedicatedTenantPermissionRepairError as exc:
        print(json.dumps({"result": "failed", "error": str(exc)}, indent=2))
        return 2
    except Exception as exc:
        print(
            json.dumps(
                {"result": "failed", "error": f"{type(exc).__name__}: {exc}"},
                indent=2,
            )
        )
        return 1

    if args.apply and args.validate_http:
        sub = report.tenant.get("subdominio") or args.subdominio
        if sub:
            report.validation = validate_admin_api_http(
                base_url=args.base_url,
                subdominio=str(sub),
                password=args.password,
                username=args.username,
                fe_port=args.fe_port,
            )

    payload = report.to_dict()
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))

    if report.result == "failed":
        return 1
    if args.apply and args.validate_http and not report.validation.get("passed"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
