#!/usr/bin/env python3
"""QA ROLE_DEACTIVATE fix — DELETE role returns 200 + RolRead."""
from __future__ import annotations

import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.lib.http_smoke_client import HttpSmokeClient
from scripts.lib.http_smoke_runner import tenant_origin

EVIDENCE = (
    PROJECT_ROOT
    / "app/bootstrap_v2/00_manifest/evidence/ROLE_DEACTIVATE_500_FIX_VALIDATION.json"
)
SUB = "t3usr971acefb"
ADMIN_PASS = "w7vO8$O&A@FQ"
CLIENTE_ID = "e4c8e906-0e64-4f4e-a04d-8daee57dc7f8"
FE_PORT = "5173"
BASE_URL = "http://localhost:8000"


def main() -> int:
    client = HttpSmokeClient(base_url=BASE_URL)
    hdr = {"Origin": tenant_origin(SUB, FE_PORT), "X-Client-Type": "mobile"}

    login = client.request(
        "POST",
        "/api/v1/auth/login/",
        headers=hdr,
        form_body={"username": "admin", "password": ADMIN_PASS},
    )
    if login.status != 200:
        report = {"verdict": {"status": "FAIL", "reason": "admin_login"}}
        EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
        EVIDENCE.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return 1

    token = login.body.get("access_token")
    auth = {**hdr, "Authorization": f"Bearer {token}"}

    suffix = uuid.uuid4().hex[:6]
    create = client.request(
        "POST",
        "/api/v1/roles/",
        headers=auth,
        json_body={
            "nombre": f"QA_DEL_{suffix}",
            "descripcion": "role deactivate fix QA",
            "cliente_id": CLIENTE_ID,
        },
    )
    rid = create.body.get("rol_id") if isinstance(create.body, dict) else None

    delete = client.request("DELETE", f"/api/v1/roles/{rid}/", headers=auth)
    body = delete.body if isinstance(delete.body, dict) else {}

    list_r = client.request("GET", "/api/v1/roles/all-active/", headers=auth)
    active_ids = []
    if isinstance(list_r.body, list):
        active_ids = [str(r.get("rol_id")).lower() for r in list_r.body if isinstance(r, dict)]

    report = {
        "report": "ROLE_DEACTIVATE_500_FIX_VALIDATION",
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "fix": "desactivar_rol returns obtener_rol_por_id after UPDATE",
        "tenant": SUB,
        "steps": {
            "create_role": {"status": create.status, "rol_id": rid},
            "delete_role": {
                "status": delete.status,
                "body": body,
                "has_rol_id": bool(body.get("rol_id")),
                "has_nombre": bool(body.get("nombre")),
                "es_activo": body.get("es_activo"),
                "detail": body.get("detail"),
            },
            "not_in_all_active": str(rid).lower() not in active_ids if rid else None,
        },
        "validation": {
            "http_200": delete.status == 200,
            "rol_read_shape": bool(body.get("rol_id") and body.get("nombre") is not None),
            "soft_deactivated": body.get("es_activo") is False,
            "absent_from_active_list": str(rid).lower() not in active_ids if rid else False,
            "no_verificar_usuario_error": body.get("detail")
            != "Error interno al verificar el usuario",
        },
    }
    all_ok = all(report["validation"].values())
    report["verdict"] = {"status": "PASS" if all_ok else "FAIL"}

    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, ensure_ascii=False, default=str))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
