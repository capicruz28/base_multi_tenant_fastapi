#!/usr/bin/env python3
"""
Smoke HTTP reutilizable — tenant ERP (login, refresh, me, menu, org, permisos).

Uso:
  python scripts/http_smoke_tenant_rbac.py \\
    --base-url http://localhost:8000 \\
    --subdominio prueba \\
    --username admin \\
    --password '<contrasena>'

  # Salida JSON + exit 0/1
  python scripts/http_smoke_tenant_rbac.py ... --json-out reports/smoke_prueba.json

Variables de entorno (alternativa a flags):
  SMOKE_BASE_URL, SMOKE_SUBDOMINIO, SMOKE_USERNAME, SMOKE_PASSWORD
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.lib.http_smoke_runner import run_tenant_smoke  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke HTTP tenant RBAC/runtime")
    parser.add_argument(
        "--base-url",
        default=os.environ.get("SMOKE_BASE_URL", "http://localhost:8000"),
    )
    parser.add_argument("--subdominio", default=os.environ.get("SMOKE_SUBDOMINIO"))
    parser.add_argument(
        "--username",
        default=os.environ.get("SMOKE_USERNAME", "admin"),
    )
    parser.add_argument("--password", default=os.environ.get("SMOKE_PASSWORD"))
    parser.add_argument("--fe-port", default=os.environ.get("SMOKE_FE_PORT", "5173"))
    parser.add_argument("--json-out", default=None, help="Ruta opcional para guardar reporte")
    args = parser.parse_args()
    if not args.subdominio or not args.password:
        print("ERROR: --subdominio y --password (o SMOKE_*) son obligatorios", file=sys.stderr)
        return 2

    report = run_tenant_smoke(
        base_url=args.base_url.rstrip("/"),
        subdominio=args.subdominio,
        username=args.username,
        password=args.password,
        fe_port=args.fe_port,
    )
    payload = report.to_dict()
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    print(text)

    if args.json_out:
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")

    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
