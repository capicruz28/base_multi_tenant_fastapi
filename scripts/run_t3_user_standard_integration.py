#!/usr/bin/env python3
"""
T3 — Validación integración USER_STANDARD sobre tenant NUEVO (sin repair).

Checks:
  1) Onboarding crea tenant (trial)
  2) SQL: rol_permiso USER_TENANT contiene bundle (16)
  3) SQL: rol_menu_permiso USER_TENANT (puede_ver=1) = 14
  4) Crear usuario user + assign rol USER_TENANT vía API
  5) GET /auth/menu con token user => modulos contiene ORG + INV
     y no hay permisos crear/editar/eliminar; no existe SYS_ADMIN

Evidencia JSON:
  app/bootstrap_v2/00_manifest/evidence/T3_USER_STANDARD_INTEGRATION_VALIDATION.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import UUID

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _load_staging_env(env_file: Path) -> None:
    if not env_file.is_file():
        return
    staging_host = os.environ.get("STAGING_DB_HOST", "CARLOSPC")
    for line in env_file.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if not key.startswith("DB_") or key in os.environ:
            continue
        if key in ("DB_SERVER", "DB_ADMIN_SERVER") and value == "host.docker.internal":
            value = staging_host
        os.environ[key] = value


def _default_env_file() -> Path:
    for i, arg in enumerate(sys.argv):
        if arg == "--env-file" and i + 1 < len(sys.argv):
            return Path(sys.argv[i + 1])
    return PROJECT_ROOT / ".env.docker"


_load_staging_env(_default_env_file())

from sqlalchemy import text

from app.infrastructure.database.connection_async import DatabaseConnection, get_db_connection
from app.modules.tenant.application.services.user_standard_constants import (
    USER_STANDARD_MENU_GRANTS,
    USER_STANDARD_PERMISSION_CODIGOS,
)
from scripts.lib.http_smoke_client import HttpSmokeClient
from scripts.lib.http_smoke_runner import platform_origin, tenant_origin

EVIDENCE_PATH = (
    PROJECT_ROOT
    / "app/bootstrap_v2/00_manifest/evidence/T3_USER_STANDARD_INTEGRATION_VALIDATION.json"
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _platform_login(
    client: HttpSmokeClient, *, fe_port: str, username: str, password: str
) -> Optional[str]:
    resp = client.request(
        "POST",
        "/api/v1/auth/login/",
        headers={"Origin": platform_origin(fe_port), "X-Client-Type": "mobile"},
        form_body={"username": username, "password": password},
    )
    if resp.status == 200 and isinstance(resp.body, dict):
        return resp.body.get("access_token")
    return None


def _tenant_login(
    client: HttpSmokeClient,
    *,
    subdominio: str,
    fe_port: str,
    username: str,
    password: str,
) -> Optional[str]:
    origin = tenant_origin(subdominio, fe_port)
    resp = client.request(
        "POST",
        "/api/v1/auth/login/",
        headers={"Origin": origin, "X-Client-Type": "mobile"},
        form_body={"username": username, "password": password},
    )
    if resp.status != 200 or not isinstance(resp.body, dict):
        return None
    access = resp.body.get("access_token")
    if access:
        return access
    selection = resp.body.get("selection_token")
    if not selection:
        return None
    empresas = resp.body.get("empresas_disponibles") or []
    if not empresas:
        return selection
    emp_id = empresas[0].get("empresa_id") or empresas[0].get("id")
    if not emp_id:
        return selection
    sel = client.request(
        "POST",
        "/api/v1/auth/empresa/seleccionar/",
        headers={"Origin": origin, "X-Client-Type": "mobile"},
        bearer=selection,
        json_body={"empresa_id": str(emp_id)},
    )
    if sel.status == 200 and isinstance(sel.body, dict) and sel.body.get("access_token"):
        return sel.body["access_token"]
    return selection


def _create_tenant(
    client: HttpSmokeClient, *, platform_token: str, fe_port: str
) -> Dict[str, Any]:
    suffix = uuid.uuid4().hex[:8]
    subdominio = f"t3usr{suffix}"
    codigo = f"T3{suffix.upper()[:5]}"
    payload = {
        "codigo_cliente": codigo,
        "subdominio": subdominio,
        "razon_social": f"T3 USER_STANDARD Tenant {suffix}",
        "nombre_comercial": f"T3USR {suffix}",
        "ruc": "20987654321",
        "tipo_instalacion": "shared",
        "modo_autenticacion": "local",
        "contacto_email": f"admin+{suffix}@t3usr.local",
        "contacto_nombre": "T3 Admin",
        "plan_suscripcion": "trial",
        "estado_suscripcion": "activo",
        "es_activo": True,
        "es_demo": True,
    }
    resp = client.request(
        "POST",
        "/api/v1/clientes/",
        headers={
            "Origin": platform_origin(fe_port),
            "X-Client-Type": "mobile",
            "Authorization": f"Bearer {platform_token}",
        },
        json_body=payload,
    )
    if resp.status not in (200, 201) or not isinstance(resp.body, dict):
        return {"ok": False, "status": resp.status, "body": resp.body}
    cred = resp.body.get("credenciales_iniciales") or {}
    data = resp.body.get("data") or {}
    return {
        "ok": True,
        "subdominio": subdominio,
        "cliente_id": data.get("cliente_id"),
        "username": cred.get("nombre_usuario", "admin"),
        "password": cred.get("contrasena"),
        "raw_status": resp.status,
    }


SQL_USER_ROLE = """
SELECT rol_id
FROM rol
WHERE cliente_id = :cid AND codigo_rol = 'USER_TENANT' AND es_activo = 1
"""

SQL_RP_COUNT = """
SELECT COUNT(DISTINCT p.codigo) AS c
FROM rol_permiso rp
INNER JOIN permiso p ON p.permiso_id = rp.permiso_id AND p.es_activo = 1
WHERE rp.cliente_id = :cid
  AND rp.rol_id = :rid
  AND p.codigo IN ({codes})
"""

SQL_RMP_VER_COUNT = """
SELECT COUNT(*) AS c
FROM rol_menu_permiso
WHERE cliente_id = :cid
  AND rol_id = :rid
  AND puede_ver = 1
"""


async def _sql_snapshot(cliente_id: UUID, *, label: str) -> Dict[str, Any]:
    cid = str(cliente_id)
    codes = list(USER_STANDARD_PERMISSION_CODIGOS)
    code_ph = ", ".join(f":pc{i}" for i in range(len(codes)))
    bind = {f"pc{i}": codes[i] for i in range(len(codes))}
    sql_rp = SQL_RP_COUNT.format(codes=code_ph)
    async with get_db_connection(DatabaseConnection.ADMIN) as session:
        row = (await session.execute(text(SQL_USER_ROLE).bindparams(cid=cid))).fetchone()
        rid = row[0] if row else None
        if rid is None:
            return {"label": label, "ok": False, "error": "USER_TENANT rol no encontrado"}
        rid_str = str(rid)
        rp = (
            await session.execute(
                text(sql_rp).bindparams(**bind, cid=cid, rid=rid_str)
            )
        ).fetchone()
        rmp = (
            await session.execute(text(SQL_RMP_VER_COUNT).bindparams(cid=cid, rid=rid_str))
        ).fetchone()

    rp_count = int(rp[0] if rp else 0)
    rmp_count = int(rmp[0] if rmp else 0)
    return {
        "label": label,
        "sql_queries": {
            "user_role": SQL_USER_ROLE.strip(),
            "rp_count": sql_rp.strip(),
            "rmp_ver_count": SQL_RMP_VER_COUNT.strip(),
        },
        "counts": {
            "rol_permiso_bundle_count": rp_count,
            "rol_menu_permiso_ver_count": rmp_count,
        },
        "expected": {
            "rol_permiso_bundle_count": len(USER_STANDARD_PERMISSION_CODIGOS),
            "rol_menu_permiso_ver_count": len(USER_STANDARD_MENU_GRANTS),
        },
        "checks": {
            "rp_ok": rp_count >= len(USER_STANDARD_PERMISSION_CODIGOS),
            "rmp_ok": rmp_count >= len(USER_STANDARD_MENU_GRANTS),
        },
    }


def _user_menu_check(menu_body: Any) -> Dict[str, Any]:
    if not isinstance(menu_body, dict):
        return {"ok": False, "reason": "body_not_dict"}
    modulos = menu_body.get("modulos") or []
    if not isinstance(modulos, list):
        return {"ok": False, "reason": "modulos_not_list"}
    codigos = [m.get("codigo") for m in modulos if isinstance(m, dict)]
    has_org = "ORG" in codigos
    has_inv = "INV" in codigos
    has_sys_admin = "SYS_ADMIN" in codigos

    any_create = False
    any_edit = False
    any_delete = False
    for m in modulos:
        if not isinstance(m, dict):
            continue
        for s in m.get("secciones") or []:
            if not isinstance(s, dict):
                continue
            for menu in s.get("menus") or []:
                if not isinstance(menu, dict):
                    continue
                perms = menu.get("permisos") or {}
                if not isinstance(perms, dict):
                    continue
                any_create = any_create or bool(perms.get("crear"))
                any_edit = any_edit or bool(perms.get("editar"))
                any_delete = any_delete or bool(perms.get("eliminar"))
    return {
        "ok": True,
        "modulo_codigos": codigos,
        "has_org": has_org,
        "has_inv": has_inv,
        "has_sys_admin": has_sys_admin,
        "any_crear_true": any_create,
        "any_editar_true": any_edit,
        "any_eliminar_true": any_delete,
    }


async def run(
    *, base_url: str, fe_port: str, platform_user: str, platform_password: str
) -> Dict[str, Any]:
    client = HttpSmokeClient(base_url=base_url)
    report: Dict[str, Any] = {
        "report": "T3_USER_STANDARD_INTEGRATION_VALIDATION",
        "timestamp_utc": _utc_now(),
        "base_url": base_url,
        "repair_used": False,
        "expected_permiso_codigos_count": len(USER_STANDARD_PERMISSION_CODIGOS),
        "expected_menu_ver_count": len(USER_STANDARD_MENU_GRANTS),
        "steps": {},
    }

    platform_token = _platform_login(
        client, fe_port=fe_port, username=platform_user, password=platform_password
    )
    report["steps"]["platform_login"] = {"passed": bool(platform_token)}
    if not platform_token:
        report["verdict"] = {"status": "FAIL", "reason": "platform_login_failed"}
        return report

    created = _create_tenant(client, platform_token=platform_token, fe_port=fe_port)
    report["steps"]["onboarding_create_tenant"] = created
    if not created.get("ok"):
        report["verdict"] = {"status": "FAIL", "reason": "onboarding_failed"}
        return report

    cid = UUID(str(created["cliente_id"]))
    sub = str(created["subdominio"])
    report["tenant_created"] = {
        "cliente_id": str(cid),
        "subdominio": sub,
        "admin_username": created["username"],
        "admin_password": created["password"],
    }

    report["steps"]["sql_post_onboarding"] = await _sql_snapshot(cid, label="post_onboarding")

    admin_token = _tenant_login(
        client,
        subdominio=sub,
        fe_port=fe_port,
        username=created["username"],
        password=created["password"],
    )
    report["steps"]["admin_login"] = {"passed": bool(admin_token)}
    if not admin_token:
        report["verdict"] = {"status": "FAIL", "reason": "admin_login_failed"}
        return report

    usr_user = f"usr_t3_{sub[-4:]}"
    usr_pass = "User123!"
    create_user = client.request(
        "POST",
        "/api/v1/usuarios/",
        headers={"Origin": tenant_origin(sub, fe_port), "X-Client-Type": "mobile"},
        bearer=admin_token,
        json_body={
            "nombre_usuario": usr_user,
            "correo": f"{usr_user}@t3.local",
            "contrasena": usr_pass,
            "cliente_id": str(cid),
            "nombre": "User",
            "apellido": "Prueba",
        },
    )
    report["steps"]["user_create"] = {"status": create_user.status, "ok": create_user.status in (200, 201)}
    if create_user.status not in (200, 201) or not isinstance(create_user.body, dict):
        report["verdict"] = {"status": "FAIL", "reason": "user_create_failed", "body": create_user.body}
        return report

    usuario_id = (create_user.body.get("data") or {}).get("usuario_id") or create_user.body.get("usuario_id")
    report["steps"]["user_create"]["usuario_id"] = usuario_id

    async with get_db_connection(DatabaseConnection.ADMIN) as session:
        row = (await session.execute(text(SQL_USER_ROLE).bindparams(cid=str(cid)))).fetchone()
        user_rol_id = str(row[0]) if row else None
    if not user_rol_id:
        report["verdict"] = {"status": "FAIL", "reason": "user_role_missing"}
        return report

    assign = client.request(
        "POST",
        f"/api/v1/usuarios/{usuario_id}/roles/{user_rol_id}/",
        headers={"Origin": tenant_origin(sub, fe_port), "X-Client-Type": "mobile"},
        bearer=admin_token,
        json_body={},
    )
    report["steps"]["user_assign"] = {"status": assign.status, "ok": assign.status in (200, 201, 409)}

    report["steps"]["sql_post_assign"] = await _sql_snapshot(cid, label="post_assign")

    user_token = _tenant_login(
        client,
        subdominio=sub,
        fe_port=fe_port,
        username=usr_user,
        password=usr_pass,
    )
    report["steps"]["user_login"] = {"passed": bool(user_token)}
    if not user_token:
        report["verdict"] = {"status": "FAIL", "reason": "user_login_failed"}
        return report

    menu = client.request(
        "GET",
        "/api/v1/auth/menu",
        headers={"Origin": tenant_origin(sub, fe_port), "X-Client-Type": "mobile"},
        bearer=user_token,
    )
    check = _user_menu_check(menu.body)
    report["steps"]["user_menu"] = {"status": menu.status, "check": check}

    passed = (
        report["steps"]["sql_post_onboarding"]["checks"]["rp_ok"]
        and report["steps"]["sql_post_onboarding"]["checks"]["rmp_ok"]
        and report["steps"]["sql_post_assign"]["checks"]["rp_ok"]
        and report["steps"]["sql_post_assign"]["checks"]["rmp_ok"]
        and menu.status == 200
        and check.get("has_org")
        and check.get("has_inv")
        and not check.get("has_sys_admin")
        and not check.get("any_crear_true")
        and not check.get("any_editar_true")
        and not check.get("any_eliminar_true")
    )
    report["verdict"] = {
        "status": "PASS" if passed else "FAIL",
        "menu_ok": bool(check.get("has_org") and check.get("has_inv")),
        "no_sys_admin": not bool(check.get("has_sys_admin")),
        "no_crear": not bool(check.get("any_crear_true")),
        "no_editar": not bool(check.get("any_editar_true")),
        "no_eliminar": not bool(check.get("any_eliminar_true")),
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="T3 USER_STANDARD integration")
    parser.add_argument("--base-url", default=os.environ.get("SMOKE_BASE_URL", "http://localhost:8000"))
    parser.add_argument("--fe-port", default=os.environ.get("SMOKE_FE_PORT", "5173"))
    parser.add_argument("--platform-user", default=os.environ.get("SMOKE_PLATFORM_USER", "superadmin"))
    parser.add_argument("--platform-password", default=os.environ.get("SMOKE_PLATFORM_PASSWORD", "admin123"))
    args = parser.parse_args()

    report = asyncio.run(
        run(
            base_url=str(args.base_url),
            fe_port=str(args.fe_port),
            platform_user=str(args.platform_user),
            platform_password=str(args.platform_password),
        )
    )
    payload = json.dumps(report, indent=2, ensure_ascii=False)
    print(payload)
    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(payload, encoding="utf-8")
    return 0 if report.get("verdict", {}).get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

