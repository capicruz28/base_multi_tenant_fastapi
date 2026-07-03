"""Adaptadores DP — reutiliza onboarding existente (PR-F4-07 / ADR-F4-02)."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ValidationError
from app.core.security.password import get_password_hash
from app.core.security.password_generator import generar_contrasena_segura
from app.infrastructure.provisioning.dedicated_tenant_seed_types import (
    DedicatedTenantSeedRequest,
)
from app.modules.tenant.application.services.cliente_onboarding_service import (
    ADMIN_USERNAME,
    ClienteOnboardingService,
    SECUENCIAS_CODIGO,
)
from app.modules.tenant.application.services.minimal_erp_tenant_bootstrap_service import (
    MinimalErpTenantBootstrapService,
)
from app.modules.tenant.application.services.onboarding_rbac_service import (
    OnboardingRbacService,
)
from app.modules.tenant.application.services.owner_sync_constants import ADMIN_ROL_CODIGO
from app.modules.tenant.presentation.schemas import ClienteCreate

logger = logging.getLogger(__name__)


@dataclass
class TenantSeedState:
    roles_ids: Dict[str, UUID] = field(default_factory=dict)
    admin_rol_id: Optional[UUID] = None
    admin_usuario_id: Optional[UUID] = None
    empresa_id: Optional[UUID] = None
    admin_password_plain: Optional[str] = None


def build_cliente_create_payload(request: DedicatedTenantSeedRequest) -> ClienteCreate:
    return ClienteCreate(
        codigo_cliente=request.codigo_cliente,
        subdominio=request.subdominio,
        razon_social=request.razon_social,
        nombre_comercial=request.nombre_comercial,
        ruc=request.ruc,
        contacto_email=request.contacto_email,
        contacto_nombre=request.contacto_nombre,
        plan_suscripcion=request.plan_suscripcion or "trial",
        tipo_instalacion="dedicated",
    )


async def hydrate_tenant_seed_state(
    session: AsyncSession,
    *,
    request: DedicatedTenantSeedRequest,
    state: TenantSeedState,
    step_code: str,
) -> None:
    if step_code in {"seed_base_roles", "seed_org_empresa", "seed_admin_user", "seed_admin_empresa_link", "seed_tenant_rbac", "seed_codigo_secuencias"}:
        if state.admin_rol_id is None:
            row = await session.execute(
                text(
                    """
                    SELECT TOP 1 rol_id
                    FROM rol
                    WHERE cliente_id = :cliente_id
                      AND codigo_rol = :codigo_rol
                      AND es_activo = 1
                    """
                ),
                {"cliente_id": request.cliente_id, "codigo_rol": ADMIN_ROL_CODIGO},
            )
            admin = row.fetchone()
            if admin:
                state.admin_rol_id = admin[0]
                state.roles_ids[ADMIN_ROL_CODIGO] = admin[0]

    if step_code in {"seed_org_empresa", "seed_admin_user", "seed_admin_empresa_link", "seed_tenant_rbac", "seed_codigo_secuencias"}:
        if state.empresa_id is None:
            emp = await MinimalErpTenantBootstrapService._get_primera_empresa_activa(
                session,
                request.cliente_id,
            )
            if emp:
                state.empresa_id = emp["empresa_id"]

    if step_code in {"seed_admin_user", "seed_admin_empresa_link", "seed_tenant_rbac", "seed_codigo_secuencias"}:
        if state.admin_usuario_id is None:
            row = await session.execute(
                text(
                    """
                    SELECT TOP 1 usuario_id
                    FROM usuario
                    WHERE cliente_id = :cliente_id
                      AND nombre_usuario = :nombre_usuario
                      AND es_eliminado = 0
                    """
                ),
                {
                    "cliente_id": request.cliente_id,
                    "nombre_usuario": ADMIN_USERNAME,
                },
            )
            user = row.fetchone()
            if user:
                state.admin_usuario_id = user[0]


async def execute_tenant_seed_step(
    session: AsyncSession,
    *,
    request: DedicatedTenantSeedRequest,
    step_code: str,
    state: TenantSeedState,
) -> None:
    cliente_data = build_cliente_create_payload(request)
    if step_code == "seed_base_roles":
        state.roles_ids = await ClienteOnboardingService._insertar_roles_base(
            session,
            request.cliente_id,
        )
        state.admin_rol_id = state.roles_ids[ADMIN_ROL_CODIGO]
        return

    if step_code == "seed_org_empresa":
        result = await MinimalErpTenantBootstrapService.ensure_empresa_inicial(
            session,
            cliente_id=request.cliente_id,
            cliente_data=cliente_data,
            usuario_creacion_id=state.admin_usuario_id,
        )
        state.empresa_id = UUID(str(result["empresa_id"]))
        return

    if step_code == "seed_admin_user":
        if state.admin_rol_id is None:
            raise ValidationError(
                detail="admin_rol_id requerido antes de seed_admin_user.",
                internal_code="TENANT_SEED_ADMIN_ROLE_MISSING",
            )
        password_plain = request.admin_password or generar_contrasena_segura(12)
        state.admin_password_plain = password_plain
        state.admin_usuario_id = await ClienteOnboardingService._insertar_usuario_admin(
            session,
            cliente_id=request.cliente_id,
            cliente_data=cliente_data,
            contrasena_hash=get_password_hash(password_plain),
            admin_rol_id=state.admin_rol_id,
            empresa_id=state.empresa_id,
        )
        return

    if step_code == "seed_admin_empresa_link":
        if not state.admin_usuario_id or not state.admin_rol_id or not state.empresa_id:
            raise ValidationError(
                detail="Datos admin/empresa incompletos para seed_admin_empresa_link.",
                internal_code="TENANT_SEED_ADMIN_LINK_PREREQ",
            )
        await MinimalErpTenantBootstrapService.vincular_admin_empresa(
            session,
            cliente_id=request.cliente_id,
            usuario_id=state.admin_usuario_id,
            admin_rol_id=state.admin_rol_id,
            empresa_id=state.empresa_id,
        )
        return

    if step_code == "seed_tenant_rbac":
        if not state.admin_rol_id or not state.admin_usuario_id:
            raise ValidationError(
                detail="Admin requerido antes de seed_tenant_rbac.",
                internal_code="TENANT_SEED_RBAC_PREREQ",
            )
        await OnboardingRbacService.bootstrap_cliente_rbac(
            session,
            cliente_id=request.cliente_id,
            admin_rol_id=state.admin_rol_id,
            activado_por_usuario_id=state.admin_usuario_id,
            plan_suscripcion=request.plan_suscripcion,
        )
        return

    if step_code == "seed_codigo_secuencias":
        await ClienteOnboardingService._insertar_secuencias_codigo(
            session,
            request.cliente_id,
        )
        return

    raise ValidationError(
        detail=f"Paso tenant seed no implementado: {step_code}.",
        internal_code="TENANT_SEED_STEP_UNSUPPORTED",
    )


async def verify_tenant_seed_prerequisites(
    session: AsyncSession,
    *,
    request: DedicatedTenantSeedRequest,
) -> None:
    """Valida que catálogos S6 mínimos existan antes del seed S7."""
    permiso = await session.execute(
        text("SELECT COUNT(*) FROM permiso WHERE codigo = :codigo"),
        {"codigo": "core.app.acceder"},
    )
    permiso_count = int(permiso.scalar_one() or 0)
    if permiso_count < 1:
        raise ConflictError(
            detail="Catálogo permiso core no presente — ejecutar S6 antes de S7.",
            internal_code="TENANT_SEED_CATALOG_PREREQ_FAILED",
        )

    modulo = await session.execute(text("SELECT COUNT(*) FROM modulo"))
    modulo_count = int(modulo.scalar_one() or 0)
    if modulo_count < 1:
        raise ConflictError(
            detail="Catálogo módulos no presente — ejecutar S6 antes de S7.",
            internal_code="TENANT_SEED_CATALOG_PREREQ_FAILED",
        )


__all__ = [
    "TenantSeedState",
    "build_cliente_create_payload",
    "execute_tenant_seed_step",
    "hydrate_tenant_seed_state",
    "verify_tenant_seed_prerequisites",
]
