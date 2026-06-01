"""
Reparación idempotente de RBAC/módulos base en tenants legacy incompletos.

Reutiliza OnboardingRbacService.bootstrap_cliente_rbac (equivalente runtime a R010+R020).
No modifica tenants ya sanos (ORG+SYS_ADMIN + grants ADMIN con core.app.acceder).
"""
from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Set
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import DatabaseError
from app.infrastructure.database.connection_async import DatabaseConnection, get_db_connection
from app.shared.legacy_rbac_repair_rules import ADMIN_ROL_CODIGO, evaluate_repair_need

logger = logging.getLogger(__name__)


@dataclass
class TenantRbacSnapshot:
    cliente_id: str
    subdominio: str
    codigo_cliente: str
    cliente_modulo_count: int
    modulos_codigos: List[str]
    admin_rol_id: Optional[str]
    rol_permiso_admin_count: int
    has_core_app_acceder: bool
    needs_repair: bool
    repair_reasons: List[str] = field(default_factory=list)
    skipped: bool = False
    skip_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TenantRepairOutcome:
    cliente_id: str
    subdominio: str
    dry_run: bool
    status: str  # skipped | dry_run | repaired | failed
    before: TenantRbacSnapshot
    after: Optional[TenantRbacSnapshot] = None
    bootstrap: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if self.before:
            data["before"] = self.before.to_dict()
        if self.after:
            data["after"] = self.after.to_dict()
        return data


@dataclass
class LegacyRepairReport:
    dry_run: bool
    audited_total: int
    repair_candidates: int
    skipped_platform_or_healthy: int
    outcomes: List[TenantRepairOutcome] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dry_run": self.dry_run,
            "audited_total": self.audited_total,
            "repair_candidates": self.repair_candidates,
            "skipped_platform_or_healthy": self.skipped_platform_or_healthy,
            "outcomes": [o.to_dict() for o in self.outcomes],
        }


def _platform_cliente_ids() -> Set[str]:
    ids: Set[str] = set()
    raw = (getattr(settings, "SUPERADMIN_CLIENTE_ID", None) or "").strip()
    if raw:
        ids.add(raw.upper())
    # UUID fijo histórico en seeds
    ids.add("00000000-0000-0000-0000-000000000001")
    return ids


class LegacyTenantRbacRepairService:
    """Auditoría y reparación batch de tenants ERP incompletos."""

    @staticmethod
    def is_excluded_platform_cliente(cliente_id: UUID) -> bool:
        return str(cliente_id).upper() in _platform_cliente_ids()

    @staticmethod
    async def snapshot_tenant(
        session: AsyncSession, cliente_id: UUID
    ) -> TenantRbacSnapshot:
        sql = text("""
            SELECT
                c.cliente_id,
                c.subdominio,
                c.codigo_cliente,
                (SELECT COUNT(*) FROM cliente_modulo cm
                 WHERE cm.cliente_id = c.cliente_id AND cm.esta_activo = 1) AS cm_count,
                (SELECT STRING_AGG(m.codigo, ',') WITHIN GROUP (ORDER BY m.codigo)
                 FROM cliente_modulo cm
                 INNER JOIN modulo m ON m.modulo_id = cm.modulo_id
                 WHERE cm.cliente_id = c.cliente_id AND cm.esta_activo = 1) AS modulos_csv,
                (SELECT TOP 1 r.rol_id FROM rol r
                 WHERE r.cliente_id = c.cliente_id
                   AND r.codigo_rol = :admin_rol
                   AND r.es_activo = 1) AS admin_rol_id,
                (SELECT COUNT(*) FROM rol_permiso rp
                 INNER JOIN rol r ON r.rol_id = rp.rol_id
                   AND r.cliente_id = c.cliente_id
                   AND r.codigo_rol = :admin_rol
                 WHERE rp.cliente_id = c.cliente_id) AS rp_admin_count,
                (SELECT CASE WHEN EXISTS (
                    SELECT 1 FROM rol_permiso rp
                    INNER JOIN rol r ON r.rol_id = rp.rol_id
                      AND r.cliente_id = c.cliente_id
                      AND r.codigo_rol = :admin_rol
                    INNER JOIN permiso p ON p.permiso_id = rp.permiso_id
                    WHERE rp.cliente_id = c.cliente_id
                      AND p.codigo = 'core.app.acceder'
                      AND p.es_activo = 1
                ) THEN 1 ELSE 0 END) AS has_core
            FROM cliente c
            WHERE c.cliente_id = :cliente_id AND c.es_activo = 1
        """).bindparams(
            cliente_id=cliente_id,
            admin_rol=ADMIN_ROL_CODIGO,
        )
        row = (await session.execute(sql)).fetchone()
        if not row:
            raise DatabaseError(
                detail=f"Cliente {cliente_id} no encontrado o inactivo.",
                internal_code="LEGACY_REPAIR_CLIENTE_NOT_FOUND",
            )

        modulos_csv = row[4]
        modulos = [m.strip() for m in str(modulos_csv).split(",") if m and m.strip()] if modulos_csv else []
        admin_rid = row[5]
        admin_rol_id = UUID(str(admin_rid)) if admin_rid else None

        needs, reasons, skipped, skip_reason = evaluate_repair_need(
            cliente_modulo_count=int(row[3] or 0),
            modulos_codigos=modulos,
            admin_rol_id=admin_rol_id,
            rol_permiso_admin_count=int(row[6] or 0),
            has_core_app_acceder=bool(row[7]),
        )

        return TenantRbacSnapshot(
            cliente_id=str(row[0]),
            subdominio=str(row[1]),
            codigo_cliente=str(row[2]),
            cliente_modulo_count=int(row[3] or 0),
            modulos_codigos=modulos,
            admin_rol_id=str(admin_rol_id) if admin_rol_id else None,
            rol_permiso_admin_count=int(row[6] or 0),
            has_core_app_acceder=bool(row[7]),
            needs_repair=needs and not skipped,
            repair_reasons=reasons,
            skipped=skipped,
            skip_reason=skip_reason,
        )

    @staticmethod
    async def list_active_tenant_ids(
        session: AsyncSession,
        *,
        cliente_ids: Optional[Sequence[UUID]] = None,
    ) -> List[UUID]:
        if cliente_ids:
            ids = [UUID(str(x)) for x in cliente_ids]
            placeholders = ", ".join(f":id{i}" for i in range(len(ids)))
            bind = {f"id{i}": ids[i] for i in range(len(ids))}
            sql = text(f"""
                SELECT cliente_id FROM cliente
                WHERE es_activo = 1 AND cliente_id IN ({placeholders})
                ORDER BY subdominio
            """).bindparams(**bind)
        else:
            sql = text("""
                SELECT cliente_id FROM cliente
                WHERE es_activo = 1
                ORDER BY subdominio
            """)
        rows = (await session.execute(sql)).fetchall()
        return [UUID(str(r[0])) for r in rows]

    @staticmethod
    async def audit_tenants(
        session: AsyncSession,
        *,
        cliente_ids: Optional[Sequence[UUID]] = None,
    ) -> List[TenantRbacSnapshot]:
        snapshots: List[TenantRbacSnapshot] = []
        for cid in await LegacyTenantRbacRepairService.list_active_tenant_ids(
            session, cliente_ids=cliente_ids
        ):
            snap = await LegacyTenantRbacRepairService.snapshot_tenant(session, cid)
            if LegacyTenantRbacRepairService.is_excluded_platform_cliente(cid):
                snap.skipped = True
                snap.skip_reason = "PLATFORM_TENANT_EXCLUDED"
                snap.needs_repair = False
                snap.repair_reasons = []
            snapshots.append(snap)
        return snapshots

    @staticmethod
    async def repair_one(
        session: AsyncSession,
        *,
        cliente_id: UUID,
        dry_run: bool,
    ) -> TenantRepairOutcome:
        before = await LegacyTenantRbacRepairService.snapshot_tenant(session, cliente_id)

        if before.skipped:
            return TenantRepairOutcome(
                cliente_id=before.cliente_id,
                subdominio=before.subdominio,
                dry_run=dry_run,
                status="skipped",
                before=before,
                error=before.skip_reason,
            )

        if not before.needs_repair:
            return TenantRepairOutcome(
                cliente_id=before.cliente_id,
                subdominio=before.subdominio,
                dry_run=dry_run,
                status="skipped",
                before=before,
                error="ALREADY_HEALTHY",
            )

        if dry_run:
            return TenantRepairOutcome(
                cliente_id=before.cliente_id,
                subdominio=before.subdominio,
                dry_run=True,
                status="dry_run",
                before=before,
            )

        if not before.admin_rol_id:
            return TenantRepairOutcome(
                cliente_id=before.cliente_id,
                subdominio=before.subdominio,
                dry_run=False,
                status="failed",
                before=before,
                error="ADMIN_TENANT_MISSING",
            )

        try:
            from app.modules.tenant.application.services.onboarding_rbac_service import (
                OnboardingRbacService,
            )

            bootstrap = await OnboardingRbacService.bootstrap_cliente_rbac(
                session,
                cliente_id=cliente_id,
                admin_rol_id=UUID(before.admin_rol_id),
                activado_por_usuario_id=None,
            )
            after = await LegacyTenantRbacRepairService.snapshot_tenant(session, cliente_id)
            return TenantRepairOutcome(
                cliente_id=before.cliente_id,
                subdominio=before.subdominio,
                dry_run=False,
                status="repaired",
                before=before,
                after=after,
                bootstrap=bootstrap,
            )
        except Exception as exc:
            logger.exception("Legacy RBAC repair failed cliente=%s", cliente_id)
            return TenantRepairOutcome(
                cliente_id=before.cliente_id,
                subdominio=before.subdominio,
                dry_run=False,
                status="failed",
                before=before,
                error=f"{type(exc).__name__}: {exc}",
            )

    @staticmethod
    async def run_batch(
        *,
        dry_run: bool = True,
        cliente_ids: Optional[Sequence[UUID]] = None,
        only_candidates: bool = True,
    ) -> LegacyRepairReport:
        """
        Audita todos los tenants activos y opcionalmente repara candidatos.

        Cada tenant reparado usa su propia transacción (commit solo si dry_run=False).
        """
        outcomes: List[TenantRepairOutcome] = []
        snapshots: List[TenantRbacSnapshot] = []

        async with get_db_connection(DatabaseConnection.ADMIN) as session:
            snapshots = await LegacyTenantRbacRepairService.audit_tenants(
                session, cliente_ids=cliente_ids
            )

        candidates = [
            s
            for s in snapshots
            if s.needs_repair and not s.skipped
        ]

        for snap in snapshots:
            if only_candidates and not snap.needs_repair:
                continue
            if snap.skipped and snap.skip_reason == "PLATFORM_TENANT_EXCLUDED":
                continue

            cid = UUID(snap.cliente_id)
            async with get_db_connection(DatabaseConnection.ADMIN) as session:
                if dry_run:
                    outcome = await LegacyTenantRbacRepairService.repair_one(
                        session, cliente_id=cid, dry_run=True
                    )
                else:
                    async with session.begin():
                        outcome = await LegacyTenantRbacRepairService.repair_one(
                            session, cliente_id=cid, dry_run=False
                        )
                outcomes.append(outcome)

        skipped_count = sum(
            1
            for s in snapshots
            if s.skipped or not s.needs_repair
        )

        return LegacyRepairReport(
            dry_run=dry_run,
            audited_total=len(snapshots),
            repair_candidates=len(candidates),
            skipped_platform_or_healthy=skipped_count,
            outcomes=outcomes,
        )


def report_to_json(report: LegacyRepairReport, *, indent: int = 2) -> str:
    return json.dumps(report.to_dict(), indent=indent, ensure_ascii=False)
