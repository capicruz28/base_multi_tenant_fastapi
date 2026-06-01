#!/usr/bin/env python3
"""
Validación de integración M0+M1+M2 en staging (OwnerSync trial + menú Owner).

Flujo:
  1. Crear tenant trial vía onboarding API
  2. Verificar SQL (cliente_modulo, rol_permiso inv.*, rol_menu_permiso)
  3. Login tenant_admin → GET /auth/menu
  4. Login platform_admin → smoke plataforma
  5. Impersonación → INV visible
  6. MANAGER_TENANT sin grants → INV no visible
  7. Evidencia JSON + SQL

Uso:
  python scripts/run_m1_m2_staging_integration.py
  python scripts/run_m1_m2_staging_integration.py --base-url http://localhost:8000
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _load_staging_env(env_file: Path) -> None:
    """Carga variables DB desde .env.docker (API staging) sin pisar las ya definidas."""
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
from app.modules.tenant.application.services.owner_sync_constants import (
    ADMIN_ROL_CODIGO,
    MIN_HEALTHY_TRIAL_OWNER_MENU_GRANTS,
    TRIAL_MODULES,
)
from scripts.lib.http_smoke_client import HttpSmokeClient
from scripts.lib.http_smoke_runner import platform_origin, run_platform_smoke, tenant_origin

EVIDENCE_PATH = (
    PROJECT_ROOT / "app/bootstrap_v2/00_manifest/evidence/M1_M2_STAGING_INTEGRATION_VALIDATION.json"
)
EXPECTED_TRIAL_MODULES = list(TRIAL_MODULES)
MANAGER_ROL_CODIGO = "MANAGER_TENANT"


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


def _create_tenant(
    client: HttpSmokeClient,
    *,
    platform_token: str,
    fe_port: str,
) -> Dict[str, Any]:
    suffix = uuid.uuid4().hex[:8]
    subdominio = f"m1m2rc{suffix}"
    codigo = f"M2{suffix.upper()[:5]}"
    payload = {
        "codigo_cliente": codigo,
        "subdominio": subdominio,
        "razon_social": f"M1M2 Integration Tenant {suffix}",
        "nombre_comercial": f"M1M2RC {suffix}",
        "ruc": "20123456789",
        "tipo_instalacion": "shared",
        "modo_autenticacion": "local",
        "contacto_email": f"admin+{suffix}@m1m2-rc.local",
        "contacto_nombre": "Integration Admin",
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


def _parse_menu(body: Any) -> Dict[str, Any]:
    if not isinstance(body, dict):
        return {"modulo_codigos": [], "forbidden_menu_codigos": [], "menu_codigos_sample": []}
    modulo_codigos: List[str] = []
    forbidden_menu_codigos: List[str] = []
    menu_codigos_sample: List[str] = []
    for mod in body.get("modulos") or []:
        if not isinstance(mod, dict):
            continue
        mod_code = str(mod.get("codigo", "")).upper()
        if mod_code:
            modulo_codigos.append(mod_code)
        for sec in mod.get("secciones") or []:
            if not isinstance(sec, dict):
                continue
            for item in sec.get("menus") or []:
                if not isinstance(item, dict):
                    continue
                cod = str(item.get("codigo") or "")
                if cod:
                    menu_codigos_sample.append(cod)
                if "SYS_ADMIN.CATALOGOS" in cod or "SYS_ADMIN.PLATFORM" in cod:
                    forbidden_menu_codigos.append(cod)
    return {
        "modulo_codigos": modulo_codigos,
        "forbidden_menu_codigos": forbidden_menu_codigos,
        "menu_codigos_sample": menu_codigos_sample[:30],
    }


async def _create_manager_via_sql(
    *,
    cliente_id: UUID,
    suffix: str,
) -> Dict[str, Any]:
    """Crea usuario MANAGER_TENANT sin grants INV (OwnerSync no aplica a MANAGER)."""
    from app.core.security.password import get_password_hash

    username = f"manager_{suffix}"
    password = "Manager123!"
    async with get_db_connection(DatabaseConnection.ADMIN) as session:
        existing = (
            await session.execute(
                text(
                    "SELECT usuario_id FROM usuario WHERE cliente_id=:cid AND nombre_usuario=:u"
                ).bindparams(cid=str(cliente_id), u=username)
            )
        ).fetchone()
        if existing:
            usuario_id = str(existing[0])
        else:
            usuario_id = str(uuid.uuid4())
            await session.execute(
                text("""
                    INSERT INTO usuario (
                        usuario_id, cliente_id, nombre_usuario, correo, contrasena,
                        nombre, apellido, proveedor_autenticacion, es_activo, correo_confirmado, es_eliminado
                    ) VALUES (
                        :uid, :cid, :u, :mail, :pwd, N'Manager', N'Test', N'local', 1, 0, 0
                    )
                """).bindparams(
                    uid=usuario_id,
                    cid=str(cliente_id),
                    u=username,
                    mail=f"{username}@m1m2-rc.local",
                    pwd=get_password_hash(password),
                )
            )
        mgr_rol = (
            await session.execute(
                text("""
                    SELECT rol_id FROM rol
                    WHERE cliente_id=:cid AND codigo_rol=:codigo AND es_activo=1
                """).bindparams(cid=str(cliente_id), codigo=MANAGER_ROL_CODIGO)
            )
        ).fetchone()
        if not mgr_rol:
            return {"ok": False, "step": "resolve_manager_rol_sql"}
        rol_id = str(mgr_rol[0])
        ur = (
            await session.execute(
                text("""
                    SELECT 1 FROM usuario_rol
                    WHERE usuario_id=:uid AND rol_id=:rid AND es_activo=1
                """).bindparams(uid=usuario_id, rid=rol_id)
            )
        ).fetchone()
        if not ur:
            await session.execute(
                text("""
                    INSERT INTO usuario_rol (usuario_rol_id, usuario_id, rol_id, cliente_id, es_activo)
                    VALUES (:urid, :uid, :rid, :cid, 1)
                """).bindparams(urid=str(uuid.uuid4()), uid=usuario_id, rid=rol_id, cid=str(cliente_id))
            )
        await session.commit()
    return {
        "ok": True,
        "username": username,
        "password": password,
        "usuario_id": usuario_id,
        "rol_id": rol_id,
        "via": "sql",
    }


async def _sql_validation(cliente_id: UUID) -> Dict[str, Any]:
    cid = str(cliente_id)
    async with get_db_connection(DatabaseConnection.ADMIN) as session:
        modulos = (
            await session.execute(
                text("""
                    SELECT m.codigo
                    FROM cliente_modulo cm
                    INNER JOIN modulo m ON m.modulo_id = cm.modulo_id
                    WHERE cm.cliente_id = :cid AND cm.esta_activo = 1
                    ORDER BY m.codigo
                """).bindparams(cid=cid)
            )
        ).fetchall()
        modulos_list = [str(r[0]) for r in modulos]

        inv_perms = (
            await session.execute(
                text("""
                    SELECT p.codigo
                    FROM rol_permiso rp
                    INNER JOIN rol r ON r.rol_id = rp.rol_id
                    INNER JOIN permiso p ON p.permiso_id = rp.permiso_id
                    WHERE rp.cliente_id = :cid
                      AND r.codigo_rol = :admin_rol
                      AND p.codigo LIKE N'inv.%'
                      AND p.es_activo = 1
                    ORDER BY p.codigo
                """).bindparams(cid=cid, admin_rol=ADMIN_ROL_CODIGO)
            )
        ).fetchall()
        inv_perm_codes = [str(r[0]) for r in inv_perms]

        menu_grants = (
            await session.execute(
                text("""
                    SELECT mm.codigo, m.codigo AS modulo_codigo
                    FROM rol_menu_permiso rmp
                    INNER JOIN rol r ON r.rol_id = rmp.rol_id
                    INNER JOIN modulo_menu mm ON mm.menu_id = rmp.menu_id
                    INNER JOIN modulo m ON m.modulo_id = mm.modulo_id
                    WHERE rmp.cliente_id = :cid
                      AND r.codigo_rol = :admin_rol
                      AND rmp.empresa_id IS NULL
                    ORDER BY m.codigo, mm.codigo
                """).bindparams(cid=cid, admin_rol=ADMIN_ROL_CODIGO)
            )
        ).fetchall()
        menu_by_modulo: Dict[str, List[str]] = {}
        all_menu_codes: List[str] = []
        for row in menu_grants:
            menu_code = str(row[0])
            mod_code = str(row[1])
            all_menu_codes.append(menu_code)
            menu_by_modulo.setdefault(mod_code, []).append(menu_code)

        forbidden_rmp = [c for c in all_menu_codes if "SYS_ADMIN.PLATFORM" in c or "SYS_ADMIN.CATALOGOS" in c]

        manager_rmp_inv = int(
            (
                await session.execute(
                    text("""
                        SELECT COUNT(*)
                        FROM rol_menu_permiso rmp
                        INNER JOIN rol r ON r.rol_id = rmp.rol_id
                        INNER JOIN modulo_menu mm ON mm.menu_id = rmp.menu_id
                        INNER JOIN modulo m ON m.modulo_id = mm.modulo_id
                        WHERE rmp.cliente_id = :cid
                          AND r.codigo_rol = :manager_rol
                          AND m.codigo = N'INV'
                    """).bindparams(cid=cid, manager_rol=MANAGER_ROL_CODIGO)
                )
            ).scalar()
            or 0
        )

        manager_rp_inv = int(
            (
                await session.execute(
                    text("""
                        SELECT COUNT(*)
                        FROM rol_permiso rp
                        INNER JOIN rol r ON r.rol_id = rp.rol_id
                        INNER JOIN permiso p ON p.permiso_id = rp.permiso_id
                        WHERE rp.cliente_id = :cid
                          AND r.codigo_rol = :manager_rol
                          AND p.codigo LIKE N'inv.%'
                    """).bindparams(cid=cid, manager_rol=MANAGER_ROL_CODIGO)
                )
            ).scalar()
            or 0
        )

        admin_rol_id_row = (
            await session.execute(
                text("""
                    SELECT rol_id FROM rol
                    WHERE cliente_id = :cid AND codigo_rol = :admin_rol AND es_activo = 1
                """).bindparams(cid=cid, admin_rol=ADMIN_ROL_CODIGO)
            )
        ).fetchone()
        manager_rol_id_row = (
            await session.execute(
                text("""
                    SELECT rol_id FROM rol
                    WHERE cliente_id = :cid AND codigo_rol = :manager_rol AND es_activo = 1
                """).bindparams(cid=cid, manager_rol=MANAGER_ROL_CODIGO)
            )
        ).fetchone()

    org_menus = menu_by_modulo.get("ORG", [])
    sys_admin_menus = [c for c in menu_by_modulo.get("SYS_ADMIN", []) if c.startswith("SYS_ADMIN.TENANT.")]
    inv_menus = menu_by_modulo.get("INV", [])

    checks = {
        "cliente_modulo_org_sys_inv": sorted(modulos_list) == sorted(EXPECTED_TRIAL_MODULES),
        "cliente_modulo_contains_all_trial": all(m in modulos_list for m in EXPECTED_TRIAL_MODULES),
        "rol_permiso_inv_present": len(inv_perm_codes) > 0,
        "rol_permiso_all_inv_prefix": all(c.startswith("inv.") for c in inv_perm_codes),
        "rol_menu_permiso_org": len(org_menus) >= 6,
        "rol_menu_permiso_sys_admin_tenant": len(sys_admin_menus) >= 3,
        "rol_menu_permiso_inv": len(inv_menus) >= 1,
        "rol_menu_permiso_min_healthy": len(all_menu_codes) >= MIN_HEALTHY_TRIAL_OWNER_MENU_GRANTS,
        "no_platform_catalogos_rmp": len(forbidden_rmp) == 0,
        "manager_no_inv_rmp": manager_rmp_inv == 0,
        "manager_no_inv_rp": manager_rp_inv == 0,
    }

    return {
        "cliente_modulo": modulos_list,
        "expected_cliente_modulo": EXPECTED_TRIAL_MODULES,
        "rol_permiso_admin_inv": {
            "count": len(inv_perm_codes),
            "sample": inv_perm_codes[:15],
            "all_inv_prefix": all(c.startswith("inv.") for c in inv_perm_codes),
        },
        "rol_menu_permiso_admin": {
            "total": len(all_menu_codes),
            "min_expected": MIN_HEALTHY_TRIAL_OWNER_MENU_GRANTS,
            "by_modulo": {k: v for k, v in menu_by_modulo.items()},
            "org_count": len(org_menus),
            "sys_admin_tenant_count": len(sys_admin_menus),
            "inv_count": len(inv_menus),
            "forbidden_platform_catalogos": forbidden_rmp,
        },
        "manager_tenant_grants": {
            "rol_id": str(manager_rol_id_row[0]) if manager_rol_id_row else None,
            "inv_rol_permiso_count": manager_rp_inv,
            "inv_rol_menu_permiso_count": manager_rmp_inv,
        },
        "admin_rol_id": str(admin_rol_id_row[0]) if admin_rol_id_row else None,
        "checks": checks,
        "passed": all(checks.values()),
        "sql_queries_used": [
            "cliente_modulo activos por modulo.codigo",
            "rol_permiso ADMIN_TENANT WHERE permiso.codigo LIKE 'inv.%'",
            "rol_menu_permiso ADMIN_TENANT JOIN modulo_menu JOIN modulo",
            "rol_menu_permiso/rol_permiso MANAGER_TENANT inv counts",
        ],
    }


def _resolve_manager_rol_id(client: HttpSmokeClient, *, bearer: str, origin: str) -> Optional[str]:
    resp = client.request(
        "GET",
        "/api/v1/roles/all-active/",
        headers={"Origin": origin, "X-Client-Type": "mobile"},
        bearer=bearer,
    )
    if resp.status != 200 or not isinstance(resp.body, list):
        return None
    for rol in resp.body:
        if isinstance(rol, dict) and str(rol.get("codigo_rol", "")).upper() == MANAGER_ROL_CODIGO:
            return str(rol.get("rol_id"))
    return None


def _create_manager_user(
    client: HttpSmokeClient,
    *,
    bearer: str,
    origin: str,
    cliente_id: str,
    suffix: str,
) -> Dict[str, Any]:
    manager_username = f"manager_{suffix}"
    manager_password = "Manager123!"
    create_resp = client.request(
        "POST",
        "/api/v1/usuarios/",
        headers={"Origin": origin, "X-Client-Type": "mobile"},
        bearer=bearer,
        json_body={
            "cliente_id": cliente_id,
            "nombre_usuario": manager_username,
            "correo": f"{manager_username}@m1m2-rc.local",
            "nombre": "Manager",
            "apellido": "Test",
            "contrasena": manager_password,
        },
    )
    if create_resp.status not in (200, 201) or not isinstance(create_resp.body, dict):
        return {
            "ok": False,
            "step": "create_user",
            "status": create_resp.status,
            "body": create_resp.body,
        }
    usuario_id = str(create_resp.body.get("usuario_id"))
    rol_id = _resolve_manager_rol_id(client, bearer=bearer, origin=origin)
    if not rol_id:
        return {"ok": False, "step": "resolve_manager_rol", "usuario_id": usuario_id}
    assign_resp = client.request(
        "POST",
        f"/api/v1/usuarios/{usuario_id}/roles/{rol_id}/",
        headers={"Origin": origin, "X-Client-Type": "mobile"},
        bearer=bearer,
        json_body={},
    )
    if assign_resp.status not in (200, 201):
        return {
            "ok": False,
            "step": "assign_role",
            "status": assign_resp.status,
            "body": assign_resp.body,
            "usuario_id": usuario_id,
            "rol_id": rol_id,
        }
    return {
        "ok": True,
        "username": manager_username,
        "password": manager_password,
        "usuario_id": usuario_id,
        "rol_id": rol_id,
    }


async def run_integration(*, base_url: str, fe_port: str, platform_user: str, platform_password: str) -> Dict[str, Any]:
    started = time.time()
    evidence: Dict[str, Any] = {
        "report": "M1_M2_STAGING_INTEGRATION_VALIDATION",
        "spec_version": "OwnerSync-v1.0+M2",
        "timestamp_utc": _utc_now(),
        "base_url": base_url,
        "steps": {},
        "verdict": {"status": "PENDING"},
    }

    client = HttpSmokeClient(base_url=base_url)

    # --- health ---
    health_ok = False
    for path in ("/health", "/api/v1/health"):
        try:
            h = client.request("GET", path)
            if h.status == 200:
                health_ok = True
                break
        except Exception:
            continue
    evidence["steps"]["health"] = {"passed": health_ok}
    if not health_ok:
        evidence["verdict"] = {"status": "FAIL", "reason": "API health check failed"}
        return evidence

    # --- 1. platform login + create tenant ---
    platform_token = _platform_login(
        client, fe_port=fe_port, username=platform_user, password=platform_password
    )
    if not platform_token:
        evidence["steps"]["platform_login"] = {"passed": False}
        evidence["verdict"] = {"status": "FAIL", "reason": "platform login failed"}
        return evidence
    evidence["steps"]["platform_login"] = {"passed": True}

    tenant = _create_tenant(client, platform_token=platform_token, fe_port=fe_port)
    evidence["steps"]["onboarding_create_tenant"] = tenant
    if not tenant.get("ok") or not tenant.get("cliente_id"):
        evidence["verdict"] = {"status": "FAIL", "reason": "tenant onboarding failed"}
        return evidence

    cliente_id = UUID(str(tenant["cliente_id"]))
    subdominio = tenant["subdominio"]
    admin_user = tenant["username"]
    admin_pass = tenant["password"]
    origin = tenant_origin(subdominio, fe_port)
    suffix = subdominio.replace("m1m2rc", "")

    evidence["tenant_created"] = {
        "cliente_id": str(cliente_id),
        "subdominio": subdominio,
        "username": admin_user,
        "password": admin_pass,
    }

    # --- 2. SQL validation ---
    sql_result = await _sql_validation(cliente_id)
    evidence["steps"]["sql_validation"] = sql_result
    evidence["sql_validation"] = sql_result

    # --- 3. tenant admin login + menu ---
    admin_token = _tenant_login(
        client,
        subdominio=subdominio,
        fe_port=fe_port,
        username=admin_user,
        password=admin_pass,
    )
    admin_menu_step: Dict[str, Any] = {"passed": False}
    if admin_token:
        menu_resp = client.request(
            "GET",
            "/api/v1/auth/menu",
            headers={"Origin": origin, "X-Client-Type": "mobile"},
            bearer=admin_token,
        )
        parsed = _parse_menu(menu_resp.body if menu_resp.status == 200 else None)
        checks = {
            "ORG": "ORG" in parsed["modulo_codigos"],
            "SYS_ADMIN": "SYS_ADMIN" in parsed["modulo_codigos"],
            "INV": "INV" in parsed["modulo_codigos"],
            "no_platform_or_catalogos": len(parsed["forbidden_menu_codigos"]) == 0,
        }
        admin_menu_step = {
            "passed": menu_resp.status == 200 and all(checks.values()),
            "status": menu_resp.status,
            "modulo_codigos": parsed["modulo_codigos"],
            "checks": checks,
            "forbidden_menu_codigos": parsed["forbidden_menu_codigos"],
            "menu_codigos_sample": parsed["menu_codigos_sample"],
        }
    else:
        admin_menu_step["login_failed"] = True
    evidence["steps"]["tenant_admin_menu"] = admin_menu_step

    # --- 4. platform admin smoke ---
    platform_smoke = run_platform_smoke(
        base_url=base_url,
        username=platform_user,
        password=platform_password,
        fe_port=fe_port,
    )
    evidence["steps"]["platform_admin_smoke"] = platform_smoke.to_dict()

    # --- 5. impersonation ---
    imp_step: Dict[str, Any] = {"passed": False}
    imp_resp = client.request(
        "POST",
        f"/api/v1/auth/impersonate/{cliente_id}/",
        headers={"Origin": platform_origin(fe_port), "X-Client-Type": "mobile"},
        bearer=platform_token,
    )
    imp_token = None
    if imp_resp.status == 200 and isinstance(imp_resp.body, dict):
        imp_token = imp_resp.body.get("access_token") or imp_resp.body.get("selection_token")
    elif imp_resp.status in (200, 201):
        imp_token = getattr(imp_resp.body, "get", lambda *_: None)("access_token") if imp_resp.body else None

    if imp_token:
        imp_menu = client.request(
            "GET",
            "/api/v1/auth/menu",
            headers={"Origin": origin, "X-Client-Type": "mobile"},
            bearer=imp_token,
        )
        imp_parsed = _parse_menu(imp_menu.body if imp_menu.status == 200 else None)
        imp_checks = {
            "ORG": "ORG" in imp_parsed["modulo_codigos"],
            "INV": "INV" in imp_parsed["modulo_codigos"],
            "no_platform_or_catalogos": len(imp_parsed["forbidden_menu_codigos"]) == 0,
        }
        imp_step = {
            "passed": imp_menu.status == 200 and imp_checks["INV"] and imp_checks["no_platform_or_catalogos"],
            "impersonate_status": imp_resp.status,
            "menu_status": imp_menu.status,
            "modulo_codigos": imp_parsed["modulo_codigos"],
            "checks": imp_checks,
            "forbidden_menu_codigos": imp_parsed["forbidden_menu_codigos"],
        }
    else:
        imp_step = {
            "passed": False,
            "impersonate_status": imp_resp.status,
            "body": imp_resp.body,
        }
    evidence["steps"]["impersonation_menu"] = imp_step

    # --- 6. MANAGER_TENANT without grants ---
    manager_step: Dict[str, Any] = {"passed": False}
    mgr = await _create_manager_via_sql(cliente_id=cliente_id, suffix=suffix)
    manager_step["user_setup"] = mgr
    if mgr.get("ok"):
        mgr_token = _tenant_login(
            client,
            subdominio=subdominio,
            fe_port=fe_port,
            username=mgr["username"],
            password=mgr["password"],
        )
        if mgr_token:
            mgr_menu = client.request(
                "GET",
                "/api/v1/auth/menu",
                headers={"Origin": origin, "X-Client-Type": "mobile"},
                bearer=mgr_token,
            )
            mgr_parsed = _parse_menu(mgr_menu.body if mgr_menu.status == 200 else None)
            mgr_checks = {
                "INV_absent": "INV" not in mgr_parsed["modulo_codigos"],
                "no_platform_or_catalogos": len(mgr_parsed["forbidden_menu_codigos"]) == 0,
            }
            manager_step.update(
                {
                    "passed": mgr_menu.status == 200 and mgr_checks["INV_absent"],
                    "menu_status": mgr_menu.status,
                    "modulo_codigos": mgr_parsed["modulo_codigos"],
                    "checks": mgr_checks,
                }
            )
            evidence["tenant_created"]["manager_username"] = mgr["username"]
            evidence["tenant_created"]["manager_password"] = mgr["password"]
        else:
            manager_step["login_failed"] = True
    evidence["steps"]["manager_tenant_menu"] = manager_step

    # Re-fetch SQL for manager grants post-setup
    sql_after_manager = await _sql_validation(cliente_id)
    evidence["sql_validation_after_manager"] = {
        "manager_tenant_grants": sql_after_manager["manager_tenant_grants"],
        "checks": {
            "manager_no_inv_rmp": sql_after_manager["checks"]["manager_no_inv_rmp"],
            "manager_no_inv_rp": sql_after_manager["checks"]["manager_no_inv_rp"],
        },
    }

    # --- verdict ---
    all_pass = (
        sql_result["passed"]
        and admin_menu_step.get("passed")
        and platform_smoke.passed
        and imp_step.get("passed")
        and manager_step.get("passed")
    )
    evidence["verdict"] = {
        "status": "PASS" if all_pass else "FAIL",
        "duration_sec": round(time.time() - started, 2),
        "summary": {
            "sql_validation": sql_result["passed"],
            "tenant_admin_menu": admin_menu_step.get("passed"),
            "platform_admin_smoke": platform_smoke.passed,
            "impersonation_inv_visible": imp_step.get("passed"),
            "manager_inv_hidden": manager_step.get("passed"),
        },
    }
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description="M1+M2 staging integration validation")
    parser.add_argument("--base-url", default=os.environ.get("SMOKE_BASE_URL", "http://localhost:8000"))
    parser.add_argument("--fe-port", default=os.environ.get("SMOKE_FE_PORT", "5173"))
    parser.add_argument("--platform-user", default=os.environ.get("SMOKE_PLATFORM_USER", "superadmin"))
    parser.add_argument("--platform-password", default=os.environ.get("SMOKE_PLATFORM_PASSWORD", "admin123"))
    parser.add_argument(
        "--env-file",
        default=str(PROJECT_ROOT / ".env.docker"),
        help="Env file for staging DB (default: .env.docker → bd_sistema_saas)",
    )
    args = parser.parse_args()

    evidence = asyncio.run(
        run_integration(
            base_url=args.base_url,
            fe_port=args.fe_port,
            platform_user=args.platform_user,
            platform_password=args.platform_password,
        )
    )

    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(json.dumps(evidence, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(evidence["verdict"], indent=2))
    print(f"\nEvidence written: {EVIDENCE_PATH}")
    return 0 if evidence.get("verdict", {}).get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
