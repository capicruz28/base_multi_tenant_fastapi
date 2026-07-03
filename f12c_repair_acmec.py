"""F12-C repair — acmec dedicated permission catalog sync + global grants."""
from __future__ import annotations

import asyncio
import json
from uuid import UUID

from sqlalchemy import text

from app.infrastructure.database.connection_async import DatabaseConnection
from app.infrastructure.database.queries_async import execute_query
from app.infrastructure.provisioning.dedicated_permission_catalog_sync_service import (
    SCRIPT_CODE,
    DedicatedPermissionCatalogSyncService,
)
from app.infrastructure.provisioning.dedicated_permission_catalog_sync_types import (
    DedicatedPermissionCatalogSyncRequest,
)
from app.infrastructure.provisioning.provisioning_dedicated_session import (
    provisioning_dedicated_session,
)
from app.modules.tenant.application.services.onboarding_rbac_service import (
    OnboardingRbacService,
)
from app.modules.tenant.application.services.owner_sync_constants import ADMIN_ROL_CODIGO
from scripts.lib.http_smoke_client import HttpSmokeClient
from scripts.lib.http_smoke_runner import tenant_origin

ACMEC_ID = UUID("6061C95E-CB3F-4BFE-9BCE-7607DE70549E")
DB = "erp_cli013"
SUB = "acmec"
PWD = "F11Gate!acmec2026"
BASE = "http://localhost:8000"


async def sql_snapshot(session, label: str) -> dict:
    async def fetch(sql: str):
        r = await session.execute(text(sql))
        return [dict(row) for row in r.mappings().all()]

    admin_permiso = await fetch(
        "SELECT codigo, modulo_id FROM permiso WHERE codigo LIKE 'admin.%' AND es_activo=1 ORDER BY codigo"
    )
    totals = await fetch(
        "SELECT COUNT(*) AS total, "
        "SUM(CASE WHEN codigo LIKE 'admin.%' THEN 1 ELSE 0 END) AS admin_count "
        "FROM permiso WHERE es_activo=1"
    )
    admin_rp = await fetch(
        """
        SELECT p.codigo FROM rol_permiso rp
        JOIN permiso p ON p.permiso_id = rp.permiso_id
        JOIN rol r ON r.rol_id = rp.rol_id
        WHERE r.codigo_rol = 'ADMIN_TENANT' AND p.codigo LIKE 'admin.%'
        ORDER BY p.codigo
        """
    )
    marker = await fetch(
        f"SELECT script_code, checksum_sha256 FROM bootstrap_applied "
        f"WHERE script_code = '{SCRIPT_CODE}'"
    )
    return {
        "label": label,
        "permiso_total": totals[0]["total"] if totals else 0,
        "admin_permiso_count": totals[0]["admin_count"] if totals else 0,
        "admin_permiso_codigos": [r["codigo"] for r in admin_permiso],
        "admin_rol_permiso_codigos": [r["codigo"] for r in admin_rp],
        "admin_rol_permiso_count": len(admin_rp),
        "sync_marker": marker[0] if marker else None,
    }


def http_snapshot() -> dict:
    client = HttpSmokeClient(base_url=BASE)
    origin = tenant_origin(SUB)
    hdrs = {"Origin": origin, "X-Client-Type": "mobile"}
    login = client.request(
        "POST",
        "/api/v1/auth/login/",
        headers=hdrs,
        form_body={"username": "admin", "password": PWD},
    )
    if login.status != 200 or not isinstance(login.body, dict):
        return {"login": login.status, "error": login.body}

    bearer = login.body.get("access_token")
    refresh = login.body.get("refresh_token")
    org = client.request("GET", "/api/v1/org/empresa", headers=hdrs, bearer=bearer)
    if org.status == 200 and isinstance(org.body, list) and org.body:
        eid = org.body[0].get("empresa_id") or org.body[0].get("id")
        if eid:
            ch = client.request(
                "POST",
                "/api/v1/auth/empresa/cambiar/",
                headers=hdrs,
                bearer=bearer,
                json_body={"empresa_id": str(eid), "refresh_token": refresh},
            )
            if ch.status == 200 and isinstance(ch.body, dict) and ch.body.get("access_token"):
                bearer = ch.body["access_token"]

    perms = client.request("GET", "/api/v1/auth/permissions/me", headers=hdrs, bearer=bearer)
    codes = []
    if isinstance(perms.body, dict):
        raw = perms.body.get("permissions") or perms.body.get("permisos") or []
        for p in raw:
            if isinstance(p, str):
                codes.append(p)
            elif isinstance(p, dict) and p.get("codigo"):
                codes.append(str(p["codigo"]))

    usuarios = client.request(
        "GET", "/api/v1/usuarios/?page=1&limit=10", headers=hdrs, bearer=bearer
    )
    roles = client.request(
        "GET", "/api/v1/roles/?page=1&limit=10", headers=hdrs, bearer=bearer
    )
    return {
        "permissions_me_status": perms.status,
        "perm_count": len(codes),
        "admin_usuario_leer": "admin.usuario.leer" in codes,
        "admin_rol_leer": "admin.rol.leer" in codes,
        "usuarios_status": usuarios.status,
        "roles_status": roles.status,
    }


async def main():
    report: dict = {}

    async with provisioning_dedicated_session(DB) as session:
        report["before_sql"] = await sql_snapshot(session, "before")

    report["before_http"] = http_snapshot()

    sync_service = DedicatedPermissionCatalogSyncService()
    sync_result = await sync_service.run_sync(
        DedicatedPermissionCatalogSyncRequest(
            database_name=DB,
            cliente_id=ACMEC_ID,
        )
    )
    report["sync_result"] = {
        "status": sync_result.status,
        "registry_hash": sync_result.registry_hash,
        "inserted": sync_result.inserted,
        "updated": sync_result.updated,
        "deactivated": sync_result.deactivated,
        "declared_count": sync_result.declared_count,
    }

    grants_result = {}
    async with provisioning_dedicated_session(DB) as session:
        row = await session.execute(
            text(
                """
                SELECT TOP 1 rol_id FROM rol
                WHERE cliente_id = :cliente_id AND codigo_rol = :codigo_rol AND es_activo = 1
                """
            ),
            {"cliente_id": str(ACMEC_ID), "codigo_rol": ADMIN_ROL_CODIGO},
        )
        admin_rol = row.fetchone()
        if not admin_rol:
            grants_result["error"] = "ADMIN_TENANT rol not found"
        else:
            admin_rol_id = admin_rol[0]
            before_rp = await sql_snapshot(session, "before_grants_in_tx")
            grants = await OnboardingRbacService.bootstrap_global_grants_admin_tenant(
                session,
                cliente_id=ACMEC_ID,
                admin_rol_id=admin_rol_id,
            )
            grants_result = {
                "inserted": grants.get("inserted", 0),
                "admin_rol_id": str(admin_rol_id),
                "sample_codigos": grants.get("sample_codigos", [])[:15],
            }
            report["after_sql"] = await sql_snapshot(session, "after")

    report["grants_result"] = grants_result
    report["after_http"] = http_snapshot()

    report["delta"] = {
        "permiso_total": report["after_sql"]["permiso_total"]
        - report["before_sql"]["permiso_total"],
        "admin_permiso_count": report["after_sql"]["admin_permiso_count"]
        - report["before_sql"]["admin_permiso_count"],
        "admin_rol_permiso_count": report["after_sql"]["admin_rol_permiso_count"]
        - report["before_sql"]["admin_rol_permiso_count"],
        "new_admin_permiso": sorted(
            set(report["after_sql"]["admin_permiso_codigos"])
            - set(report["before_sql"]["admin_permiso_codigos"])
        ),
        "new_admin_rol_permiso": sorted(
            set(report["after_sql"]["admin_rol_permiso_codigos"])
            - set(report["before_sql"]["admin_rol_permiso_codigos"])
        ),
    }

    shared_ref = await execute_query(
        text(
            """
            SELECT COUNT(*) AS n FROM permiso p
            WHERE p.es_activo=1 AND p.codigo LIKE 'admin.usuario.%'
            """
        ),
        connection_type=DatabaseConnection.DEFAULT,
        client_id=str(ACMEC_ID),
    )
    report["equivalent_to_f12b"] = {
        "sync_marker_present": report["after_sql"]["sync_marker"] is not None,
        "admin_usuario_leer_in_permiso": "admin.usuario.leer"
        in report["after_sql"]["admin_permiso_codigos"],
        "admin_usuario_leer_granted": "admin.usuario.leer"
        in report["after_sql"]["admin_rol_permiso_codigos"],
        "usuarios_200": report["after_http"].get("usuarios_status") == 200,
        "roles_200": report["after_http"].get("roles_status") == 200,
    }

    print(json.dumps(report, default=str, indent=2))


asyncio.run(main())
