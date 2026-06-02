#!/usr/bin/env python3
"""QA DELETE /clientes/{id}/ — await execute_update fix."""
from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.lib.http_smoke_client import HttpSmokeClient
from scripts.lib.http_smoke_runner import platform_origin

EVIDENCE = (
    PROJECT_ROOT
    / "app/bootstrap_v2/00_manifest/evidence/DELETE_CLIENTE_500_FIX_VALIDATION.json"
)
BASE_URL = os.environ.get("SMOKE_BASE_URL", "http://localhost:8000")
FE_PORT = os.environ.get("SMOKE_FE_PORT", "5173")
PLATFORM_USER = os.environ.get("SMOKE_PLATFORM_USER", "superadmin")
PLATFORM_PASS = os.environ.get("SMOKE_PLATFORM_PASSWORD", "admin123")
SYSTEM_CLIENTE_ID = os.environ.get(
    "SUPERADMIN_CLIENTE_ID", "00000000-0000-0000-0000-000000000001"
)


def _platform_headers(token: str) -> dict:
    return {
        "Origin": platform_origin(FE_PORT),
        "X-Client-Type": "mobile",
        "Authorization": f"Bearer {token}",
    }


def _login(client: HttpSmokeClient) -> str | None:
    resp = client.request(
        "POST",
        "/api/v1/auth/login/",
        headers={"Origin": platform_origin(FE_PORT), "X-Client-Type": "mobile"},
        form_body={"username": PLATFORM_USER, "password": PLATFORM_PASS},
    )
    if resp.status == 200 and isinstance(resp.body, dict):
        return resp.body.get("access_token")
    return None


def main() -> int:
    client = HttpSmokeClient(base_url=BASE_URL.rstrip("/"))
    report: dict = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "base_url": BASE_URL,
        "scenarios": [],
        "passed": False,
    }

    token = _login(client)
    if not token:
        report["scenarios"].append(
            {"name": "login", "ok": False, "status": None, "detail": "no token"}
        )
        EVIDENCE.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 1

    report["scenarios"].append({"name": "login", "ok": True, "status": 200})

    suffix = uuid.uuid4().hex[:8]
    create_payload = {
        "codigo_cliente": f"DL{suffix.upper()[:6]}",
        "subdominio": f"delqa{suffix}",
        "razon_social": f"DELETE QA Tenant {suffix}",
        "nombre_comercial": f"DELQA {suffix}",
        "ruc": "20123456789",
        "tipo_instalacion": "shared",
        "modo_autenticacion": "local",
        "contacto_email": f"delqa+{suffix}@qa.local",
        "contacto_nombre": "DELETE QA",
        "plan_suscripcion": "trial",
        "estado_suscripcion": "activo",
        "es_activo": True,
        "es_demo": True,
    }
    create_resp = client.request(
        "POST",
        "/api/v1/clientes/",
        headers=_platform_headers(token),
        json_body=create_payload,
    )
    cliente_id = None
    if create_resp.status in (200, 201) and isinstance(create_resp.body, dict):
        data = create_resp.body.get("data") or {}
        cliente_id = data.get("cliente_id")
    report["scenarios"].append(
        {
            "name": "create_fixture_cliente",
            "ok": bool(cliente_id),
            "status": create_resp.status,
            "cliente_id": cliente_id,
        }
    )

    if cliente_id:
        del_ok = client.request(
            "DELETE",
            f"/api/v1/clientes/{cliente_id}/",
            headers=_platform_headers(token),
        )
        report["scenarios"].append(
            {
                "name": "delete_existing_cliente",
                "ok": del_ok.status == 200,
                "expected_status": 200,
                "status": del_ok.status,
                "body": del_ok.body,
            }
        )

    missing_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    del_404 = client.request(
        "DELETE",
        f"/api/v1/clientes/{missing_id}/",
        headers=_platform_headers(token),
    )
    report["scenarios"].append(
        {
            "name": "delete_nonexistent_cliente",
            "ok": del_404.status == 404,
            "expected_status": 404,
            "status": del_404.status,
            "error_code": (del_404.body or {}).get("error_code")
            if isinstance(del_404.body, dict)
            else None,
        }
    )

    del_400 = client.request(
        "DELETE",
        f"/api/v1/clientes/{SYSTEM_CLIENTE_ID}/",
        headers=_platform_headers(token),
    )
    report["scenarios"].append(
        {
            "name": "delete_system_cliente",
            "ok": del_400.status == 400,
            "expected_status": 400,
            "status": del_400.status,
            "error_code": (del_400.body or {}).get("error_code")
            if isinstance(del_400.body, dict)
            else None,
            "detail": (del_400.body or {}).get("detail")
            if isinstance(del_400.body, dict)
            else None,
        }
    )

    report["passed"] = all(s.get("ok") for s in report["scenarios"])
    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
