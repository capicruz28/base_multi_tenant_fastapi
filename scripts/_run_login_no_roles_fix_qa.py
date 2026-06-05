#!/usr/bin/env python3
"""QA LOGIN_NO_ROLES fix — 5 login scenarios."""
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

EVIDENCE = PROJECT_ROOT / "app/bootstrap_v2/00_manifest/evidence/LOGIN_NO_ROLES_500_FIX_VALIDATION.json"
SUB = "t3usr971acefb"
ADMIN_PASS = "w7vO8$O&A@FQ"
CLIENTE_ID = "e4c8e906-0e64-4f4e-a04d-8daee57dc7f8"
FE_PORT = "5173"
BASE_URL = "http://localhost:8000"
USER_WITHOUT_COMPANY = "USER_WITHOUT_COMPANY"


def _origin_hdr() -> dict:
    return {"Origin": tenant_origin(SUB, FE_PORT), "X-Client-Type": "mobile"}


def _auth_login(
    client: HttpSmokeClient, username: str, password: str
) -> tuple[int, dict | list | str | None]:
    r = client.request(
        "POST",
        "/api/v1/auth/login/",
        headers=_origin_hdr(),
        form_body={"username": username, "password": password},
    )
    body = r.body if isinstance(r.body, (dict, list)) else str(r.body)
    return r.status, body


def _admin_token(client: HttpSmokeClient) -> str | None:
    st, body = _auth_login(client, "admin", ADMIN_PASS)
    if st == 200 and isinstance(body, dict):
        return body.get("access_token")
    return None


def _resolve_roles(client: HttpSmokeClient, token: str) -> dict[str, str]:
    """Map codigo_rol or nombre → rol_id."""
    r = client.request(
        "GET",
        "/api/v1/roles/all-active/",
        headers={**_origin_hdr(), "Authorization": f"Bearer {token}"},
    )
    out: dict[str, str] = {}
    if not isinstance(r.body, list):
        return out
    for row in r.body:
        if not isinstance(row, dict):
            continue
        rid = row.get("rol_id")
        if not rid:
            continue
        codigo = (row.get("codigo_rol") or "").upper()
        nombre = (row.get("nombre") or "").lower()
        if codigo in ("USER_TENANT", "MANAGER_TENANT", "ADMIN_TENANT"):
            out[codigo] = str(rid)
        if nombre == "usuario":
            out.setdefault("USER_TENANT", str(rid))
        if nombre in ("supervisor", "manager"):
            out.setdefault("MANAGER_TENANT", str(rid))
        if nombre == "administrador":
            out.setdefault("ADMIN_TENANT", str(rid))
    return out


def _create_user(client: HttpSmokeClient, token: str, label: str) -> tuple[str, str, str]:
    suffix = uuid.uuid4().hex[:6]
    user = f"qa_login_{label}_{suffix}"
    pwd = "QaLogin123!"
    r = client.request(
        "POST",
        "/api/v1/usuarios/",
        headers={**_origin_hdr(), "Authorization": f"Bearer {token}"},
        json_body={
            "nombre_usuario": user,
            "correo": f"{user}@t3.local",
            "contrasena": pwd,
            "cliente_id": CLIENTE_ID,
        },
    )
    uid = ""
    if isinstance(r.body, dict):
        uid = str(r.body.get("usuario_id") or "")
    return user, pwd, uid


def _assign_role(
    client: HttpSmokeClient, token: str, usuario_id: str, rol_id: str
) -> int:
    r = client.request(
        "POST",
        f"/api/v1/usuarios/{usuario_id}/roles/{rol_id}/",
        headers={**_origin_hdr(), "Authorization": f"Bearer {token}"},
        json_body={},
    )
    return r.status


def main() -> int:
    client = HttpSmokeClient(base_url=BASE_URL)
    report: dict = {
        "report": "LOGIN_NO_ROLES_500_FIX_VALIDATION",
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "fix": "endpoints.login except CustomException: raise",
        "tenant": SUB,
        "cases": {},
    }

    token = _admin_token(client)
    if not token:
        report["verdict"] = {"status": "FAIL", "reason": "admin_login"}
        EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
        EVIDENCE.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report, indent=2))
        return 1

    roles = _resolve_roles(client, token)

    # Caso 1: sin roles → 403 USER_WITHOUT_COMPANY
    u1, p1, _ = _create_user(client, token, "norole")
    st1, body1 = _auth_login(client, u1, p1)
    err1 = body1.get("error_code") if isinstance(body1, dict) else None
    report["cases"]["1_no_roles"] = {
        "username": u1,
        "expected_status": 403,
        "status": st1,
        "error_code": err1,
        "detail": body1.get("detail") if isinstance(body1, dict) else body1,
        "ok": st1 == 403 and err1 == USER_WITHOUT_COMPANY,
    }

    # Caso 2: USER_TENANT → 200
    u2, p2, id2 = _create_user(client, token, "user")
    rid_user = roles.get("USER_TENANT")
    assign2 = _assign_role(client, token, id2, rid_user) if id2 and rid_user else 0
    st2, body2 = _auth_login(client, u2, p2)
    report["cases"]["2_user_tenant"] = {
        "username": u2,
        "rol_id": rid_user,
        "assign_status": assign2,
        "expected_status": 200,
        "status": st2,
        "has_access_token": bool(
            isinstance(body2, dict) and body2.get("access_token")
        ),
        "ok": st2 == 200 and assign2 in (200, 201),
    }

    # Caso 3: MANAGER_TENANT → 200
    u3, p3, id3 = _create_user(client, token, "manager")
    rid_mgr = roles.get("MANAGER_TENANT")
    assign3 = _assign_role(client, token, id3, rid_mgr) if id3 and rid_mgr else 0
    st3, body3 = _auth_login(client, u3, p3)
    report["cases"]["3_manager_tenant"] = {
        "username": u3,
        "rol_id": rid_mgr,
        "assign_status": assign3,
        "expected_status": 200,
        "status": st3,
        "has_access_token": bool(
            isinstance(body3, dict) and body3.get("access_token")
        ),
        "ok": st3 == 200 and assign3 in (200, 201),
    }

    # Caso 4: ADMIN_TENANT (tenant admin) → 200
    st4, body4 = _auth_login(client, "admin", ADMIN_PASS)
    report["cases"]["4_admin_tenant"] = {
        "username": "admin",
        "expected_status": 200,
        "status": st4,
        "has_access_token": bool(
            isinstance(body4, dict)
            and (body4.get("access_token") or body4.get("selection_token"))
        ),
        "ok": st4 == 200,
    }

    # Caso 5: credenciales inválidas → 401
    st5, body5 = _auth_login(client, u1, "WrongPassword99!")
    report["cases"]["5_bad_credentials"] = {
        "username": u1,
        "expected_status": 401,
        "status": st5,
        "detail": body5.get("detail") if isinstance(body5, dict) else body5,
        "ok": st5 == 401,
    }

    all_ok = all(c.get("ok") for c in report["cases"].values())
    report["roles_resolved"] = roles
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
