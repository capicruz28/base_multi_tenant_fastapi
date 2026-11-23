"""
F12-F — Reparación RBAC catálogo + grants globales en tenants Dedicated (solo desarrollo).

Pipeline (idéntico F12-C):
  1. DedicatedPermissionCatalogSync
  2. bootstrap_global_grants_admin_tenant
  3. Invalidación caches (PermissionResolver + metadata conexión)
  4. Reporte estructurado

No modifica servicios de producción; orquesta APIs existentes.
"""
from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select, text

from app.core.authorization.core_permissions import CORE_APP_ACCEDER
from app.core.authorization.permission_catalog_sync_core import (
    compute_registry_hash,
    should_deactivate_permiso,
)
from app.core.authorization.permission_catalog_sync_types import SyncMode
from app.core.authorization.permission_resolver import get_permission_resolver
from app.core.authorization.permission_startup import populate_permission_registry
from app.core.tenant.routing import (
    get_connection_metadata_async,
    invalidate_client_connection_cache,
)
from app.infrastructure.database.connection_async import DatabaseConnection, get_db_connection
from app.infrastructure.database.tables import ClienteTable
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

KEY_ADMIN_USUARIO_LEER = "admin.usuario.leer"
KEY_ADMIN_ROL_LEER = "admin.rol.leer"


@dataclass(frozen=True, slots=True)
class DedicatedTenantTarget:
    cliente_id: UUID
    subdominio: str
    codigo_cliente: str
    database_name: str
    database_type: str
    tipo_instalacion: str


@dataclass
class RepairReport:
    mode: str
    tenant: dict[str, Any]
    started_at: float = field(default_factory=time.time)
    finished_at: Optional[float] = None
    duration_sec: Optional[float] = None
    result: str = "pending"
    catalog_sync: dict[str, Any] = field(default_factory=dict)
    grants: dict[str, Any] = field(default_factory=dict)
    cache: dict[str, Any] = field(default_factory=dict)
    dry_run_diff: dict[str, Any] = field(default_factory=dict)
    validation: dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def finalize(self, *, result: str) -> None:
        self.finished_at = time.time()
        self.duration_sec = round(self.finished_at - self.started_at, 3)
        self.result = result

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class DedicatedTenantPermissionRepairError(ValueError):
    """Entrada inválida o tenant no elegible para repair Dedicated."""


async def resolve_dedicated_tenant(
    *,
    cliente_id: Optional[UUID] = None,
    subdominio: Optional[str] = None,
) -> DedicatedTenantTarget:
    if cliente_id is None and not subdominio:
        raise DedicatedTenantPermissionRepairError(
            "Indique --cliente-id o --subdominio."
        )
    if cliente_id is not None and subdominio:
        raise DedicatedTenantPermissionRepairError(
            "Use solo uno: --cliente-id o --subdominio."
        )

    async with get_db_connection(DatabaseConnection.ADMIN) as session:
        if cliente_id is not None:
            query = select(
                ClienteTable.c.cliente_id,
                ClienteTable.c.subdominio,
                ClienteTable.c.codigo_cliente,
                ClienteTable.c.tipo_instalacion,
            ).where(
                ClienteTable.c.cliente_id == cliente_id,
                ClienteTable.c.es_activo == True,  # noqa: E712
            )
        else:
            query = select(
                ClienteTable.c.cliente_id,
                ClienteTable.c.subdominio,
                ClienteTable.c.codigo_cliente,
                ClienteTable.c.tipo_instalacion,
            ).where(
                ClienteTable.c.subdominio == subdominio,
                ClienteTable.c.es_activo == True,  # noqa: E712
            )
        row = (await session.execute(query)).first()
        if not row:
            raise DedicatedTenantPermissionRepairError("Tenant no encontrado o inactivo.")

        resolved_id = UUID(str(row[0]))
        resolved_sub = str(row[1])
        codigo_cliente = str(row[2])
        tipo_instalacion = str(row[3] or "shared")

    metadata = await get_connection_metadata_async(resolved_id)
    if not metadata:
        raise DedicatedTenantPermissionRepairError(
            f"Sin metadata de conexión para cliente_id={resolved_id}."
        )

    database_type = str(metadata.get("database_type") or "single")
    nombre_bd = str(metadata.get("nombre_bd") or "").strip()
    if database_type != "multi" or not nombre_bd:
        raise DedicatedTenantPermissionRepairError(
            "Repair F12-F solo aplica a tenants Dedicated (database_type=multi). "
            f"Recibido database_type={database_type!r}, nombre_bd={nombre_bd!r}."
        )

    return DedicatedTenantTarget(
        cliente_id=resolved_id,
        subdominio=resolved_sub,
        codigo_cliente=codigo_cliente,
        database_name=nombre_bd,
        database_type=database_type,
        tipo_instalacion=tipo_instalacion,
    )


async def _fetch_admin_rol_id(session, *, cliente_id: UUID) -> Optional[UUID]:
    row = (
        await session.execute(
            text(
                """
                SELECT TOP 1 rol_id FROM rol
                WHERE cliente_id = :cliente_id
                  AND codigo_rol = :codigo_rol
                  AND es_activo = 1
                """
            ),
            {"cliente_id": str(cliente_id), "codigo_rol": ADMIN_ROL_CODIGO},
        )
    ).first()
    return UUID(str(row[0])) if row else None


async def _sql_snapshot(session, *, admin_rol_id: Optional[UUID]) -> dict[str, Any]:
    async def fetch(sql: str, params: Optional[dict] = None) -> list[dict]:
        result = await session.execute(text(sql), params or {})
        return [dict(row) for row in result.mappings().all()]

    admin_permiso = await fetch(
        "SELECT codigo FROM permiso WHERE codigo LIKE 'admin.%' AND es_activo=1 ORDER BY codigo"
    )
    totals = await fetch(
        "SELECT COUNT(*) AS total, "
        "SUM(CASE WHEN codigo LIKE 'admin.%' THEN 1 ELSE 0 END) AS admin_count "
        "FROM permiso WHERE es_activo=1"
    )
    admin_rp: list[dict] = []
    if admin_rol_id:
        admin_rp = await fetch(
            """
            SELECT p.codigo FROM rol_permiso rp
            JOIN permiso p ON p.permiso_id = rp.permiso_id
            JOIN rol r ON r.rol_id = rp.rol_id
            WHERE r.rol_id = :rol_id AND p.codigo LIKE 'admin.%' AND p.es_activo = 1
            ORDER BY p.codigo
            """,
            {"rol_id": str(admin_rol_id)},
        )
    marker = await fetch(
        "SELECT script_code, checksum_sha256 FROM bootstrap_applied "
        "WHERE script_code = :script_code",
        {"script_code": SCRIPT_CODE},
    )
    codigos_admin = [r["codigo"] for r in admin_permiso]
    codigos_grants = [r["codigo"] for r in admin_rp]
    return {
        "permiso_total": int(totals[0]["total"]) if totals else 0,
        "admin_permiso_count": int(totals[0]["admin_count"] or 0) if totals else 0,
        "admin_permiso_codigos": codigos_admin,
        "admin_rol_permiso_codigos": codigos_grants,
        "admin_rol_permiso_count": len(codigos_grants),
        "has_admin_usuario_leer_permiso": KEY_ADMIN_USUARIO_LEER in codigos_admin,
        "has_admin_rol_leer_permiso": KEY_ADMIN_ROL_LEER in codigos_admin,
        "has_admin_usuario_leer_grant": KEY_ADMIN_USUARIO_LEER in codigos_grants,
        "has_admin_rol_leer_grant": KEY_ADMIN_ROL_LEER in codigos_grants,
        "sync_marker": marker[0] if marker else None,
    }


def _resolve_declared_permissions() -> list[dict[str, Any]]:
    from app.main import app as fastapi_app

    declared = populate_permission_registry(fastapi_app)
    return [dict(p) for p in declared]


async def _plan_catalog_sync(session, declared: list[dict[str, Any]]) -> dict[str, Any]:
    registry_hash = compute_registry_hash(declared)
    existing_rows = (
        await session.execute(text("SELECT codigo FROM permiso"))
    ).fetchall()
    existing_codigos = {str(row[0]) for row in existing_rows}
    declared_codigos = {p["codigo"] for p in declared}

    missing_permiso = sorted(declared_codigos - existing_codigos)
    existing_declared = sorted(declared_codigos & existing_codigos)
    would_deactivate = sorted(
        codigo
        for codigo in existing_codigos
        if should_deactivate_permiso(
            codigo, declared_codigos, SyncMode.DEDICATED_DATA_PLANE
        )
    )

    marker_row = (
        await session.execute(
            text(
                "SELECT checksum_sha256 FROM bootstrap_applied WHERE script_code = :code"
            ),
            {"code": SCRIPT_CODE},
        )
    ).first()
    marker_hash = str(marker_row[0]) if marker_row else None
    sync_would_skip = (
        marker_hash is not None and marker_hash.lower() == registry_hash.lower()
    )

    missing_admin = sorted(
        c for c in missing_permiso if c.startswith("admin.")
    )
    return {
        "registry_hash": registry_hash,
        "sync_would_skip": sync_would_skip,
        "permisos_faltantes_count": len(missing_permiso),
        "permisos_faltantes": missing_permiso,
        "permisos_faltantes_admin": missing_admin,
        "permisos_existentes_a_actualizar_count": len(existing_declared),
        "permisos_a_desactivar_count": len(would_deactivate),
        "permisos_a_desactivar_sample": would_deactivate[:20],
    }


async def _plan_global_grants(
    session, *, cliente_id: UUID, admin_rol_id: UUID
) -> dict[str, Any]:
    missing_rows = (
        await session.execute(
            text(
                """
                SELECT p.codigo
                FROM permiso p
                WHERE p.es_activo = 1
                  AND p.modulo_id IS NULL
                  AND (
                        p.codigo = :core_app_acceder
                     OR p.codigo LIKE 'admin.%'
                     OR p.codigo LIKE 'modulos.%'
                     OR (
                            p.codigo LIKE 'tenant.%'
                        AND p.codigo <> 'tenant.cliente.crear'
                     )
                  )
                  AND NOT EXISTS (
                        SELECT 1 FROM rol_permiso rp
                        WHERE rp.cliente_id = :cliente_id
                          AND rp.rol_id = :admin_rol_id
                          AND rp.permiso_id = p.permiso_id
                  )
                ORDER BY p.codigo
                """
            ),
            {
                "cliente_id": str(cliente_id),
                "admin_rol_id": str(admin_rol_id),
                "core_app_acceder": CORE_APP_ACCEDER,
            },
        )
    ).fetchall()
    missing = [str(row[0]) for row in missing_rows]

    existing_rows = (
        await session.execute(
            text(
                """
                SELECT p.codigo
                FROM rol_permiso rp
                INNER JOIN permiso p ON p.permiso_id = rp.permiso_id AND p.es_activo = 1
                WHERE rp.cliente_id = :cliente_id AND rp.rol_id = :admin_rol_id
                ORDER BY p.codigo
                """
            ),
            {"cliente_id": str(cliente_id), "admin_rol_id": str(admin_rol_id)},
        )
    ).fetchall()
    existing = [str(row[0]) for row in existing_rows]

    return {
        "grants_faltantes_count": len(missing),
        "grants_faltantes": missing,
        "grants_existentes_count": len(existing),
        "grants_existentes_admin_sample": sorted(
            c for c in existing if c.startswith("admin.")
        )[:25],
        "missing_admin_usuario_leer": KEY_ADMIN_USUARIO_LEER in missing,
        "missing_admin_rol_leer": KEY_ADMIN_ROL_LEER in missing,
    }


def invalidate_repair_caches(cliente_id: UUID) -> dict[str, Any]:
    resolver = get_permission_resolver()
    resolver.invalidate_for_tenant(cliente_id)
    metadata_invalidated = invalidate_client_connection_cache(cliente_id)
    return {
        "permission_resolver_invalidated": True,
        "connection_metadata_invalidated": metadata_invalidated,
    }


async def run_dedicated_permission_repair(
    *,
    cliente_id: Optional[UUID] = None,
    subdominio: Optional[str] = None,
    dry_run: bool = False,
) -> RepairReport:
    target = await resolve_dedicated_tenant(
        cliente_id=cliente_id, subdominio=subdominio
    )
    report = RepairReport(
        mode="dry_run" if dry_run else "apply",
        tenant={
            "cliente_id": str(target.cliente_id),
            "subdominio": target.subdominio,
            "codigo_cliente": target.codigo_cliente,
            "database_name": target.database_name,
            "database_type": target.database_type,
            "tipo_instalacion": target.tipo_instalacion,
        },
    )

    declared = _resolve_declared_permissions()

    try:
        async with provisioning_dedicated_session(target.database_name) as session:
            admin_rol_id = await _fetch_admin_rol_id(
                session, cliente_id=target.cliente_id
            )
            if admin_rol_id is None:
                raise DedicatedTenantPermissionRepairError(
                    f"Rol {ADMIN_ROL_CODIGO!r} no encontrado en BD dedicada."
                )

            before = await _sql_snapshot(session, admin_rol_id=admin_rol_id)
            catalog_plan = await _plan_catalog_sync(session, declared)
            grants_plan = await _plan_global_grants(
                session, cliente_id=target.cliente_id, admin_rol_id=admin_rol_id
            )
            report.dry_run_diff = {
                "before": before,
                "catalog": catalog_plan,
                "grants": grants_plan,
            }

            if dry_run:
                needs_work = (
                    not catalog_plan["sync_would_skip"]
                    or catalog_plan["permisos_faltantes_count"] > 0
                    or grants_plan["grants_faltantes_count"] > 0
                )
                report.catalog_sync = {
                    "status": "dry_run",
                    "would_skip": catalog_plan["sync_would_skip"],
                    "permisos_creados_estimados": catalog_plan["permisos_faltantes_count"],
                    "permisos_actualizados_estimados": (
                        0
                        if catalog_plan["sync_would_skip"]
                        else catalog_plan["permisos_existentes_a_actualizar_count"]
                    ),
                }
                report.grants = {
                    "status": "dry_run",
                    "grants_agregados_estimados": grants_plan["grants_faltantes_count"],
                    "grants_existentes": grants_plan["grants_existentes_count"],
                }
                report.finalize(
                    result="dry_run_ok" if needs_work else "dry_run_no_changes_needed"
                )
                return report

        sync_service = DedicatedPermissionCatalogSyncService()
        sync_result = await sync_service.run_sync(
            DedicatedPermissionCatalogSyncRequest(
                database_name=target.database_name,
                cliente_id=target.cliente_id,
            )
        )
        report.catalog_sync = {
            "status": sync_result.status,
            "registry_hash": sync_result.registry_hash,
            "permisos_creados": sync_result.inserted,
            "permisos_actualizados": sync_result.updated,
            "permisos_desactivados": sync_result.deactivated,
            "declared_count": sync_result.declared_count,
        }

        grants_payload: dict[str, Any] = {}
        async with provisioning_dedicated_session(target.database_name) as session:
            admin_rol_id = await _fetch_admin_rol_id(
                session, cliente_id=target.cliente_id
            )
            if admin_rol_id is None:
                raise DedicatedTenantPermissionRepairError(
                    f"Rol {ADMIN_ROL_CODIGO!r} no encontrado tras sync."
                )
            grants_before_count = (
                await session.execute(
                    text(
                        "SELECT COUNT(*) FROM rol_permiso "
                        "WHERE cliente_id = :cliente_id AND rol_id = :rol_id"
                    ),
                    {
                        "cliente_id": str(target.cliente_id),
                        "rol_id": str(admin_rol_id),
                    },
                )
            ).scalar() or 0

            grants_result = await OnboardingRbacService.bootstrap_global_grants_admin_tenant(
                session,
                cliente_id=target.cliente_id,
                admin_rol_id=admin_rol_id,
            )
            after = await _sql_snapshot(session, admin_rol_id=admin_rol_id)
            grants_after_count = len(grants_result.get("codigos") or [])

            grants_payload = {
                "status": "applied",
                "grants_agregados": int(grants_result.get("inserted") or 0),
                "grants_existentes": grants_after_count,
                "grants_antes": int(grants_before_count),
                "has_admin_usuario_leer_grant": after["has_admin_usuario_leer_grant"],
                "has_admin_rol_leer_grant": after["has_admin_rol_leer_grant"],
            }
            report.grants = grants_payload
            report.dry_run_diff["after"] = after

        report.cache = invalidate_repair_caches(target.cliente_id)
        ok = (
            after["has_admin_usuario_leer_permiso"]
            and after["has_admin_rol_leer_permiso"]
            and after["has_admin_usuario_leer_grant"]
            and after["has_admin_rol_leer_grant"]
        )
        report.finalize(result="success" if ok else "success_with_gaps")
        return report

    except Exception as exc:
        report.error = str(exc)
        report.finalize(result="failed")
        raise


def validate_admin_api_http(
    *,
    base_url: str,
    subdominio: str,
    password: str,
    username: str = "admin",
    fe_port: str = "5173",
) -> dict[str, Any]:
    """Smoke HTTP post-repair — permissions/me + usuarios + roles."""
    from scripts.lib.http_smoke_client import HttpSmokeClient
    from scripts.lib.http_smoke_runner import tenant_origin

    client = HttpSmokeClient(base_url=base_url.rstrip("/"))
    origin = tenant_origin(subdominio, fe_port)
    hdrs = {"Origin": origin, "X-Client-Type": "mobile"}

    login = client.request(
        "POST",
        "/api/v1/auth/login/",
        headers=hdrs,
        form_body={"username": username, "password": password},
    )
    if login.status != 200 or not isinstance(login.body, dict):
        return {
            "login_status": login.status,
            "error": login.body,
            "passed": False,
        }

    bearer = login.body.get("access_token")
    refresh = login.body.get("refresh_token")

    org = client.request("GET", "/api/v1/org/empresa", headers=hdrs, bearer=bearer)
    if org.status == 200 and isinstance(org.body, list) and org.body:
        emp_id = org.body[0].get("empresa_id") or org.body[0].get("id")
        if emp_id and refresh:
            ch = client.request(
                "POST",
                "/api/v1/auth/empresa/cambiar/",
                headers=hdrs,
                bearer=bearer,
                json_body={"empresa_id": str(emp_id), "refresh_token": refresh},
            )
            if ch.status == 200 and isinstance(ch.body, dict) and ch.body.get(
                "access_token"
            ):
                bearer = ch.body["access_token"]

    perms = client.request(
        "GET", "/api/v1/auth/permissions/me", headers=hdrs, bearer=bearer
    )
    codes: list[str] = []
    if isinstance(perms.body, dict):
        raw = perms.body.get("permissions") or perms.body.get("permisos") or []
        for p in raw:
            if isinstance(p, str):
                codes.append(p)
            elif isinstance(p, dict) and p.get("codigo"):
                codes.append(str(p["codigo"]))

    usuarios = client.request(
        "GET",
        "/api/v1/usuarios/?page=1&limit=10",
        headers=hdrs,
        bearer=bearer,
    )
    roles = client.request(
        "GET",
        "/api/v1/roles/?page=1&limit=10",
        headers=hdrs,
        bearer=bearer,
    )

    checks = {
        "admin_usuario_leer": KEY_ADMIN_USUARIO_LEER in codes,
        "admin_rol_leer": KEY_ADMIN_ROL_LEER in codes,
        "permissions_me_status": perms.status,
        "usuarios_status": usuarios.status,
        "roles_status": roles.status,
        "perm_count": len(codes),
    }
    checks["passed"] = (
        checks["admin_usuario_leer"]
        and checks["admin_rol_leer"]
        and checks["permissions_me_status"] == 200
        and checks["usuarios_status"] == 200
        and checks["roles_status"] == 200
    )
    return checks
