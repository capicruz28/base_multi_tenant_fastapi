"""
Fachada interna Empresa Bootstrap (Bootstrap V2 — Fase 1).

Capa de delegación pura hacia implementación AS-IS existente.
"""
from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.tenant.application.services.cfg_codigo_onboarding_seed import (
    seed_cfg_empresa,
)
from app.modules.tenant.application.services.minimal_erp_tenant_bootstrap_service import (
    MinimalErpTenantBootstrapService,
)
from app.modules.tenant.presentation.schemas import ClienteCreate


class EmpresaBootstrapService:
    """Componente interno E-ORG / E-LNK / E-CFG — delegación AS-IS (Strangler Fig)."""

    @staticmethod
    async def ensure_empresa_inicial(
        session: AsyncSession,
        *,
        cliente_id: UUID,
        cliente_data: ClienteCreate,
        usuario_creacion_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        return await MinimalErpTenantBootstrapService.ensure_empresa_inicial(
            session,
            cliente_id=cliente_id,
            cliente_data=cliente_data,
            usuario_creacion_id=usuario_creacion_id,
        )

    @staticmethod
    async def vincular_admin_empresa(
        session: AsyncSession,
        *,
        cliente_id: UUID,
        usuario_id: UUID,
        admin_rol_id: UUID,
        empresa_id: UUID,
    ) -> Dict[str, Any]:
        return await MinimalErpTenantBootstrapService.vincular_admin_empresa(
            session,
            cliente_id=cliente_id,
            usuario_id=usuario_id,
            admin_rol_id=admin_rol_id,
            empresa_id=empresa_id,
        )

    @staticmethod
    async def insertar_secuencias_codigo(
        session: AsyncSession, cliente_id: UUID, empresa_id: UUID
    ) -> None:
        await seed_cfg_empresa(session, cliente_id, empresa_id)
