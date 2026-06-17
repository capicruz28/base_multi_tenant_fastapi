"""
Orquestador bootstrap plataforma — identidad + RBAC en transacción atómica.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.connection_async import DatabaseConnection, get_db_connection
from app.modules.tenant.application.services.platform_bootstrap_audit import audit_platform_ready
from app.modules.tenant.application.services.platform_identity_bootstrap_service import (
    PlatformIdentityBootstrapService,
)
from app.modules.tenant.application.services.platform_rbac_bootstrap_service import (
    PlatformRbacBootstrapService,
)

logger = logging.getLogger(__name__)


@dataclass
class PlatformBootstrapReport:
    """Reporte consolidado bootstrap plataforma."""

    mode: str
    dry_run: bool
    audit_before: Dict[str, Any] = field(default_factory=dict)
    audit_after: Dict[str, Any] = field(default_factory=dict)
    identity: Dict[str, Any] = field(default_factory=dict)
    rbac: Dict[str, Any] = field(default_factory=dict)
    success: bool = False
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            "dry_run": self.dry_run,
            "audit_before": self.audit_before,
            "audit_after": self.audit_after,
            "identity": self.identity,
            "rbac": self.rbac,
            "success": self.success,
            "errors": self.errors,
        }


class PlatformBootstrapService:
    """CLI bootstrap plataforma: audit, identity, rbac."""

    @staticmethod
    async def audit_only() -> Dict[str, Any]:
        async with get_db_connection(DatabaseConnection.ADMIN) as session:
            return await audit_platform_ready(session)

    @staticmethod
    async def _run_identity_and_rbac(
        session: AsyncSession,
        *,
        dry_run: bool,
        rbac_only: bool,
        expose_generated_password: bool,
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        identity: Dict[str, Any] = {"skipped": rbac_only}
        if not rbac_only:
            identity_result = await PlatformIdentityBootstrapService.bootstrap_platform_identity(
                session,
                dry_run=dry_run,
                expose_generated_password=expose_generated_password,
            )
            identity = identity_result.to_dict()

        rbac: Dict[str, Any] = {"skipped": dry_run}
        if not dry_run:
            activado_por: Optional[UUID] = None
            uid_raw = identity.get("usuario_id")
            if uid_raw:
                activado_por = UUID(str(uid_raw))
            rbac_result = await PlatformRbacBootstrapService.bootstrap_platform_rbac(
                session,
                activado_por_usuario_id=activado_por,
            )
            rbac = rbac_result
        elif not rbac_only:
            rbac = {"dry_run": True, "would_run": True}
        else:
            rbac = {"dry_run": True, "would_run_rbac_only": True}

        return identity, rbac

    @classmethod
    async def bootstrap(
        cls,
        *,
        mode: str = "apply",
        dry_run: bool = False,
        rbac_only: bool = False,
        expose_generated_password: bool = False,
    ) -> PlatformBootstrapReport:
        """
        Ejecuta bootstrap según modo.

        mode: audit-only | dry-run | apply | rbac-only
        """
        report = PlatformBootstrapReport(
            mode=mode,
            dry_run=dry_run or mode == "dry-run",
        )

        try:
            async with get_db_connection(DatabaseConnection.ADMIN) as session:
                report.audit_before = await audit_platform_ready(session)

            if mode == "audit-only":
                report.audit_after = report.audit_before
                report.success = not report.audit_before.get("needs_bootstrap", True)
                return report

            if report.dry_run:
                async with get_db_connection(DatabaseConnection.ADMIN) as session:
                    identity, rbac = await cls._run_identity_and_rbac(
                        session,
                        dry_run=True,
                        rbac_only=rbac_only,
                        expose_generated_password=expose_generated_password,
                    )
                report.identity = identity
                report.rbac = rbac
                report.audit_after = report.audit_before
                report.success = True
                return report

            async with get_db_connection(DatabaseConnection.ADMIN) as session:
                async with session.begin():
                    identity, rbac = await cls._run_identity_and_rbac(
                        session,
                        dry_run=False,
                        rbac_only=rbac_only,
                        expose_generated_password=expose_generated_password,
                    )

            report.identity = identity
            report.rbac = rbac

            async with get_db_connection(DatabaseConnection.ADMIN) as session:
                report.audit_after = await audit_platform_ready(session)

            report.success = not report.audit_after.get("needs_bootstrap", True)
            return report

        except Exception as exc:
            logger.exception("bootstrap_platform failed")
            report.errors.append(str(exc))
            report.success = False
            return report

    @classmethod
    async def ensure_platform_ready(
        cls,
        *,
        dry_run: bool = False,
        rbac_only: bool = False,
        expose_generated_password: bool = False,
    ) -> PlatformBootstrapReport:
        """Alias estable para repair / integraciones."""
        mode = "dry-run" if dry_run else "apply"
        return await cls.bootstrap(
            mode=mode,
            dry_run=dry_run,
            rbac_only=rbac_only,
            expose_generated_password=expose_generated_password,
        )
