#!/usr/bin/env python3
"""
@deprecated Use scripts/bootstrap_platform.py instead.

Reparación idempotente RBAC cliente plataforma (ADMIN_PLATFORM + SYS_ADMIN).
Delega en PlatformBootstrapService (--rbac-only).

Uso legado (preferir bootstrap_platform.py --rbac-only):
  python scripts/repair_platform_rbac.py --dry-run
  python scripts/repair_platform_rbac.py --apply
  python scripts/repair_platform_rbac.py --audit-only
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import warnings
from pathlib import Path
from typing import Any, Dict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.modules.tenant.application.services.platform_bootstrap_audit import (  # noqa: E402
    audit_platform_ready,
)
from app.modules.tenant.application.services.platform_bootstrap_service import (  # noqa: E402
    PlatformBootstrapService,
)
from app.infrastructure.database.connection_async import (  # noqa: E402
    DatabaseConnection,
    get_db_connection,
)


async def _audit_only() -> int:
    async with get_db_connection(DatabaseConnection.ADMIN) as session:
        snap = await audit_platform_ready(session)
    print(json.dumps({"audit": snap}, indent=2, ensure_ascii=False))
    return 0 if not snap.get("needs_repair", True) else 1


async def _run(*, dry_run: bool) -> int:
    report = await PlatformBootstrapService.ensure_platform_ready(
        dry_run=dry_run,
        rbac_only=True,
    )
    payload: Dict[str, Any] = {
        "deprecated": True,
        "use_instead": "scripts/bootstrap_platform.py --rbac-only",
        "dry_run": report.dry_run,
        "before": report.audit_before,
        "after": report.audit_after,
        "rbac": report.rbac,
        "success": report.success,
        "errors": report.errors,
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    if report.errors:
        return 2
    after = report.audit_after or report.audit_before
    return 0 if report.success and not after.get("needs_repair", True) else 1


def main() -> int:
    warnings.warn(
        "repair_platform_rbac.py está deprecado. Use bootstrap_platform.py --rbac-only.",
        DeprecationWarning,
        stacklevel=2,
    )
    parser = argparse.ArgumentParser(description="[DEPRECATED] Platform RBAC repair")
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
