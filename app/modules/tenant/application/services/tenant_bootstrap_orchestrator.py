"""
Orquestador interno Tenant Bootstrap — Shared y Dedicated (Bootstrap V2).

Coordina secuencia T-* + invocaciones EmpresaBootstrapService dentro de la TX del caller.
Sin lógica de negocio nueva; delegación AS-IS (Strangler Fig).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.tenant.application.services.cfg_codigo_onboarding_seed import (
    seed_cfg_tenant,
)
from app.modules.tenant.application.services.empresa_bootstrap_service import (
    EmpresaBootstrapService,
)
from app.modules.tenant.application.services.onboarding_rbac_service import (
    OnboardingRbacService,
)
from app.modules.tenant.presentation.schemas import ClienteCreate


@dataclass(frozen=True)
class SharedTenantBootstrapResult:
    cliente_row: Dict[str, Any]
    cliente_id: UUID


class TenantBootstrapOrchestrator:
    """Orquestador tenant onboarding — secuencia normativa Shared y pasos S7 Dedicated."""

    @staticmethod
    async def run_seed_base_roles(
        session: AsyncSession, cliente_id: UUID
    ) -> Dict[str, UUID]:
        from app.modules.tenant.application.services.cliente_onboarding_service import (
            ClienteOnboardingService,
        )

        return await ClienteOnboardingService._insertar_roles_base(session, cliente_id)

    @staticmethod
    async def run_seed_org_empresa(
        session: AsyncSession,
        *,
        cliente_id: UUID,
        cliente_data: ClienteCreate,
        usuario_creacion_id: Optional[UUID] = None,
    ) -> UUID:
        result = await EmpresaBootstrapService.ensure_empresa_inicial(
            session,
            cliente_id=cliente_id,
            cliente_data=cliente_data,
            usuario_creacion_id=usuario_creacion_id,
        )
        return UUID(str(result["empresa_id"]))

    @staticmethod
    async def run_seed_admin_user(
        session: AsyncSession,
        *,
        cliente_id: UUID,
        cliente_data: ClienteCreate,
        contrasena_hash: str,
        admin_rol_id: UUID,
        empresa_id: Optional[UUID],
    ) -> UUID:
        from app.modules.tenant.application.services.cliente_onboarding_service import (
            ClienteOnboardingService,
        )

        return await ClienteOnboardingService._insertar_usuario_admin(
            session,
            cliente_id=cliente_id,
            cliente_data=cliente_data,
            contrasena_hash=contrasena_hash,
            admin_rol_id=admin_rol_id,
            empresa_id=empresa_id,
        )

    @staticmethod
    async def run_seed_admin_empresa_link(
        session: AsyncSession,
        *,
        cliente_id: UUID,
        usuario_id: UUID,
        admin_rol_id: UUID,
        empresa_id: UUID,
    ) -> None:
        await EmpresaBootstrapService.vincular_admin_empresa(
            session,
            cliente_id=cliente_id,
            usuario_id=usuario_id,
            admin_rol_id=admin_rol_id,
            empresa_id=empresa_id,
        )

    @staticmethod
    async def run_seed_tenant_rbac(
        session: AsyncSession,
        *,
        cliente_id: UUID,
        admin_rol_id: UUID,
        activado_por_usuario_id: UUID,
        plan_suscripcion: Optional[str],
    ) -> None:
        await OnboardingRbacService.bootstrap_cliente_rbac(
            session,
            cliente_id=cliente_id,
            admin_rol_id=admin_rol_id,
            activado_por_usuario_id=activado_por_usuario_id,
            plan_suscripcion=plan_suscripcion,
        )

    @staticmethod
    async def run_seed_codigo_secuencias(
        session: AsyncSession, *, cliente_id: UUID, empresa_id: UUID
    ) -> None:
        await seed_cfg_tenant(session, cliente_id)
        await EmpresaBootstrapService.insertar_secuencias_codigo(
            session, cliente_id, empresa_id
        )

    @staticmethod
    async def orchestrate_shared_onboarding(
        session: AsyncSession,
        cliente_data: ClienteCreate,
        contrasena_hash: str,
    ) -> SharedTenantBootstrapResult:
        from app.modules.tenant.application.services.cliente_onboarding_service import (
            ClienteOnboardingService,
        )

        cliente_row = await ClienteOnboardingService._insertar_cliente(
            session, cliente_data
        )
        cliente_id = cliente_row["cliente_id"]

        roles_ids = await TenantBootstrapOrchestrator.run_seed_base_roles(
            session, cliente_id
        )
        admin_rol_id = roles_ids["ADMIN_TENANT"]

        empresa_id = await TenantBootstrapOrchestrator.run_seed_org_empresa(
            session,
            cliente_id=cliente_id,
            cliente_data=cliente_data,
        )

        usuario_id = await TenantBootstrapOrchestrator.run_seed_admin_user(
            session,
            cliente_id=cliente_id,
            cliente_data=cliente_data,
            contrasena_hash=contrasena_hash,
            admin_rol_id=admin_rol_id,
            empresa_id=empresa_id,
        )
        await TenantBootstrapOrchestrator.run_seed_admin_empresa_link(
            session,
            cliente_id=cliente_id,
            usuario_id=usuario_id,
            admin_rol_id=admin_rol_id,
            empresa_id=empresa_id,
        )
        await TenantBootstrapOrchestrator.run_seed_tenant_rbac(
            session,
            cliente_id=cliente_id,
            admin_rol_id=admin_rol_id,
            activado_por_usuario_id=usuario_id,
            plan_suscripcion=cliente_data.plan_suscripcion,
        )
        await ClienteOnboardingService._insertar_auth_config_si_no_existe(
            session, cliente_id
        )
        await TenantBootstrapOrchestrator.run_seed_codigo_secuencias(
            session, cliente_id=cliente_id, empresa_id=empresa_id
        )

        return SharedTenantBootstrapResult(
            cliente_row=cliente_row,
            cliente_id=cliente_id,
        )
