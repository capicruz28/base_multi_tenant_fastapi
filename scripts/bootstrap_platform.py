#!/usr/bin/env python3
"""
Bootstrap plataforma — identidad (D010 A–E) + RBAC ADMIN_PLATFORM.

Uso (Docker — comando oficial):
  docker exec -w /app -e PYTHONPATH=/app fastapi_backend \\
    python scripts/bootstrap_platform.py --audit-only

  docker exec -w /app -e PYTHONPATH=/app \\
    -e PLATFORM_BOOTSTRAP_INITIAL_PASSWORD='<segura>' \\
    fastapi_backend python scripts/bootstrap_platform.py --apply
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings  # noqa: E402 — dispara load_dotenv
from app.modules.tenant.application.services.platform_bootstrap_service import (  # noqa: E402
    PlatformBootstrapService,
)


def _build_payload(report) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "dry_run": report.dry_run,
        "before": report.audit_before,
        "after": report.audit_after,
        "identity": report.identity,
        "rbac": report.rbac,
        "success": report.success,
        "errors": report.errors,
        "credentials": {
            "username": settings.SUPERADMIN_USERNAME,
            "password_generated": bool(report.identity.get("password_generated")),
        },
    }
    return payload


def _exit_code(report, *, mode: str) -> int:
    if report.errors:
        err = " ".join(report.errors).lower()
        if "password" in err and "obligatoria" in err:
            return 2
        return 2
    if mode == "audit-only":
        return 0 if not report.audit_before.get("needs_bootstrap", True) else 1
    if report.dry_run:
        return 0
    after = report.audit_after or report.audit_before
    return 0 if report.success and not after.get("needs_bootstrap", True) else 1


async def _main(args: argparse.Namespace) -> int:
    if args.audit_only:
        audit = await PlatformBootstrapService.audit_only()
        payload = {"audit": audit}
        text = json.dumps(payload, indent=2, ensure_ascii=False)
        print(text)
        if args.json_out:
            Path(args.json_out).write_text(text, encoding="utf-8")
        return 0 if not audit.get("needs_bootstrap", True) else 1

    mode = "dry-run" if args.dry_run else "apply"
    report = await PlatformBootstrapService.bootstrap(
        mode=mode,
        dry_run=args.dry_run,
        rbac_only=args.rbac_only,
        expose_generated_password=args.expose_generated_password,
    )
    payload = _build_payload(report)
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    print(text)
    if args.json_out:
        Path(args.json_out).write_text(text, encoding="utf-8")
    return _exit_code(report, mode=mode)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bootstrap plataforma (identidad + RBAC ADMIN_PLATFORM)"
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--audit-only", action="store_true", help="Solo audit JSON")
    mode.add_argument("--dry-run", action="store_true", help="Simula apply sin commit")
    mode.add_argument("--apply", action="store_true", help="Ejecuta bootstrap completo")
    mode.add_argument(
        "--rbac-only",
        action="store_true",
        help="Solo fase RBAC (compat repair_platform_rbac)",
    )
    parser.add_argument("--json-out", default=None, help="Ruta artefacto JSON evidencia")
    parser.add_argument(
        "--expose-generated-password",
        action="store_true",
        help="Dev: loguea contraseña generada (nunca en prod)",
    )
    args = parser.parse_args()
    return asyncio.run(_main(args))


if __name__ == "__main__":
    raise SystemExit(main())
