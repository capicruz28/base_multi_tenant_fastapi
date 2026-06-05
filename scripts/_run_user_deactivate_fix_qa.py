#!/usr/bin/env python3
"""QA for USER_DEACTIVATE_500 fix — delete user + DB validation."""
from __future__ import annotations

import asyncio
import json
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.lib.http_smoke_client import HttpSmokeClient
from scripts.lib.http_smoke_runner import tenant_origin

EVIDENCE = PROJECT_ROOT / "app/bootstrap_v2/00_manifest/evidence/USER_DEACTIVATE_500_FIX_VALIDATION.json"
SUB = "t3usr971acefb"
ADMIN_PASS = "w7vO8$O&A@FQ"
CLIENTE_ID = "e4c8e906-0e64-4f4e-a04d-8daee57dc7f8"
FE_PORT = "5173"
BASE_URL = "http://localhost:8000"


def _login(client: HttpSmokeClient) -> tuple[int, str | None]:
    origin = tenant_origin(SUB, FE_PORT)
    r = client.request(
        "POST",
        "/api/v1/auth/login/",
        headers={"Origin": origin, "X-Client-Type": "mobile"},
        form_body={"username": "admin", "password": ADMIN_PASS},
    )
    if r.status != 200 or not isinstance(r.body, dict):
        return r.status, None
    return r.status, r.body.get("access_token")


def _hdrs(token: str) -> dict:
    return {"Origin": tenant_origin(SUB, FE_PORT), "X-Client-Type": "mobile", "Authorization": f"Bearer {token}"}


def _preventive_scan() -> dict:
    us_path = PROJECT_ROOT / "app/modules/users/application/services/user_service.py"
    src = us_path.read_text(encoding="utf-8")
    out = {"file": str(us_path.relative_to(PROJECT_ROOT))}
    for name in ("execute_update", "execute_insert", "execute_query"):
        pattern = rf"(?<!await )= {name}\("
        out[f"{name}_without_await"] = len(re.findall(pattern, src))
    return out


def _api_db_check(client: HttpSmokeClient, token: str, usuario_id: str) -> dict:
    """Post-delete state via tenant-scoped API (same data as BD)."""
    user = client.request("GET", f"/api/v1/usuarios/{usuario_id}/", headers=_hdrs(token))
    roles = client.request("GET", f"/api/v1/usuarios/{usuario_id}/roles/", headers=_hdrs(token))
    u_body = user.body if isinstance(user.body, dict) else {}
    roles_list = roles.body if isinstance(roles.body, list) else []
    activos = sum(1 for r in roles_list if isinstance(r, dict) and r.get("es_activo"))
    return {
        "get_usuario_status": user.status,
        "usuario": {
            "usuario_id": u_body.get("usuario_id"),
            "es_eliminado": u_body.get("es_eliminado"),
            "es_activo": u_body.get("es_activo"),
            "nombre_usuario": u_body.get("nombre_usuario"),
        }
        if u_body
        else None,
        "get_roles_status": roles.status,
        "usuario_rol": {"total": len(roles_list), "activos": activos},
    }


async def _run_qa_async(client: HttpSmokeClient, token: str) -> dict:
    report: dict = {
        "report": "USER_DEACTIVATE_500_FIX_VALIDATION",
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "fix": "user_service.py L1021 await execute_update",
        "tenant": SUB,
        "preventive_scan": _preventive_scan(),
        "steps": {"admin_login": {"status": 200, "ok": True}},
    }

    suffix = uuid.uuid4().hex[:6]
    create = client.request(
        "POST",
        "/api/v1/usuarios/",
        headers=_hdrs(token),
        json_body={
            "nombre_usuario": f"qa_del_{suffix}",
            "correo": f"qa_del_{suffix}@t3.local",
            "contrasena": "QaDel123!",
            "cliente_id": CLIENTE_ID,
        },
    )
    uid = create.body.get("usuario_id") if isinstance(create.body, dict) else None
    report["steps"]["create_user_for_delete"] = {"status": create.status, "usuario_id": uid}

    roles = client.request("GET", "/api/v1/roles/all-active/", headers=_hdrs(token))
    user_rol = None
    if isinstance(roles.body, list):
        for r in roles.body:
            if isinstance(r, dict) and (r.get("nombre") or "").lower() == "usuario":
                user_rol = r.get("rol_id")
    if uid and user_rol:
        assign = client.request(
            "POST",
            f"/api/v1/usuarios/{uid}/roles/{user_rol}/",
            headers=_hdrs(token),
            json_body={},
        )
        report["steps"]["assign_rol_usuario"] = {"status": assign.status, "rol_id": user_rol}

    delete = client.request("DELETE", f"/api/v1/usuarios/{uid}/", headers=_hdrs(token))
    report["steps"]["delete_user"] = {
        "status": delete.status,
        "ok": delete.status == 200,
        "body": delete.body if isinstance(delete.body, dict) else str(delete.body)[:500],
    }

    report["steps"]["db_after_delete"] = _api_db_check(client, token, str(uid)) if uid else {}
    report["qa_usuario_id"] = uid

    del_body = report["steps"]["delete_user"].get("body") or {}
    db_after = report["steps"]["db_after_delete"]
    soft_ok = bool(del_body.get("es_eliminado")) is True
    if db_after.get("usuario") and db_after["usuario"].get("es_eliminado") is not None:
        u = db_after["usuario"]
        soft_ok = bool(u.get("es_eliminado")) and not bool(u.get("es_activo"))
    roles_ok = int((db_after.get("usuario_rol") or {}).get("activos") or 0) == 0

    report["steps"]["validation"] = {
        "soft_delete_usuario": soft_ok,
        "usuario_rol_deactivated": roles_ok,
    }
    return report


def main() -> int:
    client = HttpSmokeClient(base_url=BASE_URL)
    st, token = _login(client)
    if not token:
        report = {
            "report": "USER_DEACTIVATE_500_FIX_VALIDATION",
            "steps": {"admin_login": {"status": st, "ok": False}},
            "verdict": {"status": "FAIL", "reason": "admin_login"},
        }
        EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
        EVIDENCE.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return 1

    report = asyncio.run(_run_qa_async(client, token))
    all_ok = (
        report["steps"]["delete_user"]["status"] == 200
        and report["steps"]["validation"]["soft_delete_usuario"]
        and report["steps"]["validation"]["usuario_rol_deactivated"]
        and report["preventive_scan"]["execute_update_without_await"] == 0
    )
    report["verdict"] = {"status": "PASS" if all_ok else "FAIL"}
    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False, default=str))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
