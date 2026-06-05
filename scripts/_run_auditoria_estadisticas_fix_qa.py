#!/usr/bin/env python3
"""QA SUPERADMIN_AUDITORIA_ESTADISTICAS fix — ISO Z date filters on 3 endpoints."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.lib.http_smoke_client import HttpSmokeClient
from scripts.lib.http_smoke_runner import platform_origin

EVIDENCE = PROJECT_ROOT / (
    "app/bootstrap_v2/00_manifest/evidence/"
    "SUPERADMIN_AUDITORIA_ESTADISTICAS_500_FIX_VALIDATION.json"
)
BASE_URL = "http://localhost:8000"
PLATFORM_USER = "superadmin"
PLATFORM_PASS = "admin123"
FE_PORT = "5173"


def _platform_headers(token: str | None = None) -> dict:
    hdrs = {"Origin": platform_origin(FE_PORT), "X-Client-Type": "mobile"}
    if token:
        hdrs["Authorization"] = f"Bearer {token}"
    return hdrs


def _login(client: HttpSmokeClient) -> tuple[int, str | None]:
    r = client.request(
        "POST",
        "/api/v1/auth/login/",
        headers=_platform_headers(),
        form_body={"username": PLATFORM_USER, "password": PLATFORM_PASS},
    )
    if r.status == 200 and isinstance(r.body, dict):
        return r.status, r.body.get("access_token")
    return r.status, None


def _iso_z_range() -> tuple[str, str]:
    now = datetime.now(timezone.utc)
    desde = (now - timedelta(days=1)).replace(microsecond=233000)
    hasta = now.replace(microsecond=233000)
    return (
        quote(desde.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z", safe=""),
        quote(hasta.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z", safe=""),
    )


def main() -> int:
    client = HttpSmokeClient(base_url=BASE_URL)
    fecha_desde, fecha_hasta = _iso_z_range()
    qs = f"fecha_desde={fecha_desde}&fecha_hasta={fecha_hasta}"

    evidence: dict = {
        "fix_id": "SUPERADMIN_AUDITORIA_ESTADISTICAS_500",
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "base_url": BASE_URL,
        "date_query_sample": f"fecha_desde=...Z&fecha_hasta=...Z",
        "endpoints": {},
    }

    login_status, token = _login(client)
    evidence["login"] = {"status": login_status, "has_token": bool(token)}
    if not token:
        print(json.dumps(evidence, indent=2))
        EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
        EVIDENCE.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        return 1

    endpoints = [
        ("estadisticas", f"/api/v1/superadmin/auditoria/estadisticas/?{qs}"),
        ("autenticacion", f"/api/v1/superadmin/auditoria/autenticacion/?{qs}&limit=5"),
        ("sincronizacion", f"/api/v1/superadmin/auditoria/sincronizacion/?{qs}&limit=5"),
    ]

    all_ok = True
    for name, path in endpoints:
        r = client.request("GET", path, headers=_platform_headers(token))
        body_preview = r.body
        if isinstance(body_preview, dict):
            body_preview = {k: body_preview[k] for k in list(body_preview)[:8]}
        evidence["endpoints"][name] = {
            "path": path.split("?")[0] + "/",
            "status": r.status,
            "ok": r.status == 200,
            "body_preview": body_preview,
        }
        if r.status != 200:
            all_ok = False
        print(f"{name}: HTTP {r.status}")

    evidence["passed"] = all_ok
    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE.write_text(json.dumps(evidence, indent=2, default=str), encoding="utf-8")
    print(f"Evidence written to {EVIDENCE}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
