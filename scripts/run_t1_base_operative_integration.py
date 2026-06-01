#!/usr/bin/env python3
"""
T1 — Validación integración BASE_OPERATIVE sobre tenant NUEVO (sin repair).

Flujo:
  1. POST /api/v1/clientes/ (onboarding trial)
  2. SQL: rol_permiso BASE en MANAGER/USER (post-onboarding, sin repair)
  3. Crear usuario manager + assign rol vía API tenant admin
  4. SQL: confirmar BASE tras assign (idempotente)
  5. GET /clientes/tenant/branding con token manager
  6. Evidencia JSON

Uso:
  python scripts/run_t1_base_operative_integration.py
  python scripts/run_t1_base_operative_integration.py --base-url http://localhost:8000
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
from typing import Any, Dict, List, Optional
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
from app.modules.tenant.application.services.base_operative_constants import (
    BASE_OPERATIVE_PERMISSION_CODIGOS,
    MANAGER_ROL_CODIGO,
    USER_ROL_CODIGO,
)
from scripts.lib.http_smoke_client import HttpSmokeClient
from scripts.lib.http_smoke_runner import platform_origin, tenant_origin

EVIDENCE_PATH = (
    PROJECT_ROOT
    / "app/bootstrap_v2/00_manifest/evidence/T1_BASE_OPERATIVE_INTEGRATION_VALIDATION.json"
)

SQL_BASE_RP_BY_ROL = """
SELECT r.codigo_rol, p.codigo
FROM rol r
INNER JOIN rol_permiso rp ON rp.rol_id = r.rol_id AND rp.cliente_id = r.cliente_id
INNER JOIN permiso p ON p.permiso_id = rp.permiso_id AND p.es_activo = 1
WHERE r.cliente_id = :cid
  AND r.codigo_rol IN ('ADMIN_TENANT', 'MANAGER_TENANT', 'USER_TENANT')
  AND p.codigo IN ('core.app.acceder', 'tenant.branding.leer', 'org.empresa.leer')
ORDER BY r.codigo_rol, p.codigo
"""

SQL_ROLES = """
SELECT rol_id, codigo_rol, nombre
FROM rol
WHERE cliente_id = :cid
  AND codigo_rol IN ('ADMIN_TENANT', 'MANAGER_TENANT', 'USER_TENANT')
  AND es_activo = 1
ORDER BY codigo_rol
"""

SQL_BASE_COUNT = """
SELECT r.codigo_rol, COUNT(DISTINCT p.codigo) AS base_count
FROM rol r
LEFT JOIN rol_permiso rp ON rp.rol_id = r.rol_id AND rp.cliente_id = r.cliente_id
LEFT JOIN permiso p ON p.permiso_id = rp.permiso_id
  AND p.es_activo = 1
  AND p.codigo IN ('core.app.acceder', 'tenant.branding.leer', 'org.empresa.leer')
WHERE r.cliente_id = :cid
  AND r.codigo_rol IN ('MANAGER_TENANT', 'USER_TENANT')
GROUP BY r.codigo_rol
ORDER BY r.codigo_rol
"""


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _platform_login(client: HttpSmokeClient, *, fe_port: str, username: str, password: str) -> Optional[str]:
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


def _create_tenant(client: HttpSmokeClient, *, platform_token: str, fe_port: str) -> Dict[str, Any]:
    suffix = uuid.uuid4().hex[:8]
    subdominio = f"t1base{suffix}"
    codigo = f"T1{suffix.upper()[:5]}"
    payload = {
        "codigo_cliente": codigo,
        "subdominio": subdominio,
        "razon_social": f"T1 BASE_OPERATIVE Tenant {suffix}",
        "nombre_comercial": f"T1BASE {suffix}",
        "ruc": "20987654321",
        "tipo_instalacion": "shared",
        "modo_autenticacion": "local",
        "contacto_email": f"admin+{suffix}@t1base.local",
        "contacto_nombre": "T1 Admin",
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


async def _sql_snapshot(cliente_id: UUID, *, label: str) -> Dict[str, Any]:
    cid = str(cliente_id)
    async with get_db_connection(DatabaseConnection.ADMIN) as session:
        roles = (
            await session.execute(text(SQL_ROLES).bindparams(cid=cid))
        ).fetchall()
        base_rows = (
            await session.execute(text(SQL_BASE_RP_BY_ROL).bindparams(cid=cid))
        ).fetchall()
        counts = (
            await session.execute(text(SQL_BASE_COUNT).bindparams(cid=cid))
        ).fetchall()

    by_rol: Dict[str, List[str]] = {}
    for codigo_rol, perm in base_rows:
        by_rol.setdefault(str(codigo_rol), []).append(str(perm))

    count_map = {str(r[0]): int(r[1]) for r in counts}
    expected = len(BASE_OPERATIVE_PERMISSION_CODIGOS)

    return {
        "label": label,
        "sql_queries": {
            "roles": SQL_ROLES.strip(),
            "base_rp_by_rol": SQL_BASE_RP_BY_ROL.strip(),
            "base_count": SQL_BASE_COUNT.strip(),
        },
        "roles": [
            {"rol_id": str(r[0]), "codigo_rol": r[1], "nombre": r[2]} for r in roles
        ],
        "base_permiso_by_rol": by_rol,
        "base_count_by_rol": count_map,
        "checks": {
            "manager_base_complete": count_map.get(MANAGER_ROL_CODIGO, 0) >= expected,
            "user_base_complete": count_map.get(USER_ROL_CODIGO, 0) >= expected,
            "manager_has_all_three": set(by_rol.get(MANAGER_ROL_CODIGO, []))
            >= set(BASE_OPERATIVE_PERMISSION_CODIGOS),
            "user_has_all_three": set(by_rol.get(USER_ROL_CODIGO, []))
            >= set(BASE_OPERATIVE_PERMISSION_CODIGOS),
        },
    }


async def _create_and_assign_manager_via_api(
    client: HttpSmokeClient,
    *,
    subdominio: str,
    fe_port: str,
    admin_token: str,
    cliente_id: UUID,
    suffix: str,
) -> Dict[str, Any]:
    origin = tenant_origin(subdominio, fe_port)
    mgr_user = f"mgr_t1_{suffix}"
    mgr_pass = "Manager123!"
    mgr_mail = f"{mgr_user}@t1base.local"

    create = client.request(
        "POST",
        "/api/v1/usuarios/",
        headers={
            "Origin": origin,
            "X-Client-Type": "mobile",
            "Authorization": f"Bearer {admin_token}",
        },
        json_body={
            "cliente_id": str(cliente_id),
            "nombre_usuario": mgr_user,
            "correo": mgr_mail,
            "contrasena": mgr_pass,
            "nombre": "Manager",
            "apellido": "Prueba",
        },
    )
    if create.status not in (200, 201) or not isinstance(create.body, dict):
        return {"ok": False, "step": "create_user", "status": create.status, "body": create.body}

    usuario_id = (create.body.get("data") or create.body).get("usuario_id")
    if not usuario_id:
        usuario_id = create.body.get("usuario_id")

    async with get_db_connection(DatabaseConnection.ADMIN) as session:
        rol_row = (
            await session.execute(
                text("""
                    SELECT rol_id FROM rol
                    WHERE cliente_id = :cid AND codigo_rol = :codigo AND es_activo = 1
                """).bindparams(cid=str(cliente_id), codigo=MANAGER_ROL_CODIGO)
            )
        ).fetchone()
    if not rol_row:
        return {"ok": False, "step": "resolve_manager_rol"}
    rol_id = str(rol_row[0])

    assign = client.request(
        "POST",
        f"/api/v1/usuarios/{usuario_id}/roles/{rol_id}/",
        headers={
            "Origin": origin,
            "X-Client-Type": "mobile",
            "Authorization": f"Bearer {admin_token}",
        },
        json_body={},
    )
    if assign.status not in (200, 201) and assign.status != 409:
        return {
            "ok": False,
            "step": "assign_role",
            "status": assign.status,
            "body": assign.body,
        }

    return {
        "ok": True,
        "username": mgr_user,
        "password": mgr_pass,
        "usuario_id": str(usuario_id),
        "rol_id": rol_id,
        "via": "api_assign",
        "assign_status": assign.status,
    }


def _test_branding(
    client: HttpSmokeClient,
    *,
    subdominio: str,
    fe_port: str,
    token: str,
) -> Dict[str, Any]:
    origin = tenant_origin(subdominio, fe_port)
    resp = client.request(
        "GET",
        "/api/v1/clientes/tenant/branding",
        headers={
            "Origin": origin,
            "X-Client-Type": "mobile",
            "Authorization": f"Bearer {token}",
        },
    )
    return {
        "status": resp.status,
        "ok": resp.status == 200,
        "body_keys": list(resp.body.keys()) if isinstance(resp.body, dict) else None,
    }


async def run_integration(*, base_url: str, fe_port: str) -> Dict[str, Any]:
    client = HttpSmokeClient(base_url=base_url)
    evidence: Dict[str, Any] = {
        "report": "T1_BASE_OPERATIVE_INTEGRATION_VALIDATION",
        "timestamp_utc": _utc_now(),
        "base_url": base_url,
        "repair_used": False,
        "expected_base_codigos": list(BASE_OPERATIVE_PERMISSION_CODIGOS),
        "steps": {},
    }

    health = client.request("GET", "/health")
    evidence["steps"]["health"] = {"passed": health.status == 200, "status": health.status}
    if health.status != 200:
        evidence["verdict"] = {"status": "FAIL", "reason": "health check failed"}
        return evidence

    platform_user = os.environ.get("PLATFORM_SMOKE_USER", "superadmin")
    platform_pass = os.environ.get("PLATFORM_SMOKE_PASSWORD", "admin123")
    platform_token = _platform_login(
        client, fe_port=fe_port, username=platform_user, password=platform_pass
    )
    evidence["steps"]["platform_login"] = {"passed": bool(platform_token)}
    if not platform_token:
        evidence["verdict"] = {"status": "FAIL", "reason": "platform login failed"}
        return evidence

    tenant = _create_tenant(client, platform_token=platform_token, fe_port=fe_port)
    evidence["steps"]["onboarding_create_tenant"] = tenant
    if not tenant.get("ok"):
        evidence["verdict"] = {"status": "FAIL", "reason": "onboarding failed"}
        return evidence

    cliente_id = UUID(str(tenant["cliente_id"]))
    suffix = tenant["subdominio"].replace("t1base", "")

    sql_post_onboarding = await _sql_snapshot(cliente_id, label="post_onboarding_no_repair")
    evidence["steps"]["sql_post_onboarding"] = sql_post_onboarding

    admin_token = _tenant_login(
        client,
        subdominio=tenant["subdominio"],
        fe_port=fe_port,
        username=tenant["username"],
        password=tenant["password"],
    )
    evidence["steps"]["admin_login"] = {"passed": bool(admin_token)}

    manager = await _create_and_assign_manager_via_api(
        client,
        subdominio=tenant["subdominio"],
        fe_port=fe_port,
        admin_token=admin_token or "",
        cliente_id=cliente_id,
        suffix=suffix,
    )
    evidence["steps"]["manager_setup"] = manager

    sql_post_assign = await _sql_snapshot(cliente_id, label="post_assign_no_repair")
    evidence["steps"]["sql_post_assign"] = sql_post_assign

    manager_token = None
    branding_manager = {"ok": False, "skipped": True}
    if manager.get("ok"):
        manager_token = _tenant_login(
            client,
            subdominio=tenant["subdominio"],
            fe_port=fe_port,
            username=manager["username"],
            password=manager["password"],
        )
        evidence["steps"]["manager_login"] = {"passed": bool(manager_token)}
        if manager_token:
            branding_manager = _test_branding(
                client,
                subdominio=tenant["subdominio"],
                fe_port=fe_port,
                token=manager_token,
            )
    evidence["steps"]["manager_branding"] = branding_manager

    onboarding_ok = sql_post_onboarding["checks"]["manager_base_complete"] and sql_post_onboarding[
        "checks"
    ]["user_base_complete"]
    assign_ok = manager.get("ok")
    branding_ok = branding_manager.get("ok", False)

    if onboarding_ok:
        root_cause = "none — onboarding provisions BASE_OPERATIVE correctly"
    elif assign_ok and sql_post_assign["checks"]["manager_base_complete"]:
        root_cause = "onboarding gap; assign_role hook provisions BASE (verify onboarding hook)"
    else:
        root_cause = "onboarding and/or assign_role — BASE not provisioned without repair"

    evidence["tenant_created"] = {
        "cliente_id": str(cliente_id),
        "subdominio": tenant["subdominio"],
        "admin_username": tenant["username"],
        "admin_password": tenant["password"],
        "manager_username": manager.get("username"),
        "manager_password": manager.get("password"),
    }
    evidence["diagnosis"] = {
        "onboarding_provisions_base": onboarding_ok,
        "assign_role_path_ok": assign_ok,
        "repair_required_for_validation": not onboarding_ok,
        "repair_script_issue": "circular import fixed in constants; use docker exec if local DB host differs",
        "root_cause_assessment": root_cause,
        "branding_api_manager": branding_ok,
    }
    evidence["verdict"] = {
        "status": "PASS"
        if onboarding_ok and branding_ok and manager.get("ok")
        else "FAIL",
        "onboarding_base_operative": onboarding_ok,
        "manager_branding_200": branding_ok,
        "manager_assign_ok": assign_ok,
    }
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description="T1 BASE_OPERATIVE integration validation")
    parser.add_argument("--base-url", default=os.environ.get("API_BASE_URL", "http://localhost:8000"))
    parser.add_argument("--fe-port", default=os.environ.get("FE_PORT", "5173"))
    parser.add_argument("--output", type=Path, default=EVIDENCE_PATH)
    args = parser.parse_args()

    evidence = asyncio.run(run_integration(base_url=args.base_url, fe_port=args.fe_port))
    payload = json.dumps(evidence, indent=2, ensure_ascii=False)
    print(payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(payload, encoding="utf-8")
    print(f"\nWrote {args.output}", file=sys.stderr)

    status = evidence.get("verdict", {}).get("status", "FAIL")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
