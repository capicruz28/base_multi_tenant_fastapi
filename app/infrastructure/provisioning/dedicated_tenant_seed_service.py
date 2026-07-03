"""
DedicatedTenantSeedService — bootstrap_v2 S7 tenant seed en BD Dedicated (PR-F4-07).

Seed admin, roles, org_empresa, RBAC y secuencias en Data Plane.
Desacoplado — consumo exclusivo por orchestrator F4-08.
"""
from __future__ import annotations

import logging
import re
from contextlib import AbstractAsyncContextManager
from typing import Callable, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, DatabaseError, ValidationError
from app.infrastructure.provisioning.dedicated_database_naming import (
    assert_sql_identifier,
    escape_sql_literal,
)
from app.infrastructure.provisioning.dedicated_tenant_seed_adapters import (
    TenantSeedState,
    execute_tenant_seed_step,
    hydrate_tenant_seed_state,
    verify_tenant_seed_prerequisites,
)
from app.infrastructure.provisioning.dedicated_tenant_seed_types import (
    DedicatedTenantSeedRequest,
    DedicatedTenantSeedResult,
    TenantSeedRowVerification,
)
from app.infrastructure.provisioning.provisioning_dedicated_session import (
    provisioning_dedicated_session,
)
from app.infrastructure.provisioning.tenant_seed_profiles import (
    TenantSeedStepDefinition,
    dedupe_row_expectations,
    resolve_tenant_seed_profile,
    validate_tenant_seed_profile_integrity,
)
from app.modules.tenant.application.services.cliente_onboarding_service import (
    ADMIN_USERNAME,
)

logger = logging.getLogger(__name__)

_TABLE_NAME_RE = re.compile(r"^[A-Za-z0-9_]{1,128}$")
_STEP_CODE = "seed_tenant"

DedicatedSessionFactory = Callable[
    [str],
    AbstractAsyncContextManager[AsyncSession],
]


class DedicatedTenantSeedService:
    """Ejecutor seed tenant Dedicated S7 sobre BD ya bootstrappeada + catálogos."""

    def __init__(
        self,
        session_factory: Optional[DedicatedSessionFactory] = None,
    ) -> None:
        self._session_factory = session_factory or provisioning_dedicated_session

    async def run_tenant_seed(
        self,
        request: DedicatedTenantSeedRequest,
    ) -> DedicatedTenantSeedResult:
        assert_sql_identifier(request.database_name, field="database_name")
        profile = resolve_tenant_seed_profile(request.plan_suscripcion)
        validate_tenant_seed_profile_integrity(profile)

        state = TenantSeedState()
        executed: list[str] = []
        skipped: list[str] = []

        async with self._session_factory(request.database_name) as session:
            await verify_tenant_seed_prerequisites(session, request=request)

            for step in profile.steps:
                if await self._is_step_applied(session, step):
                    await hydrate_tenant_seed_state(
                        session,
                        request=request,
                        state=state,
                        step_code=step.step_code,
                    )
                    skipped.append(step.step_code)
                    logger.info(
                        "Tenant seed skipped cliente_id=%s database=%s step=%s",
                        request.cliente_id,
                        request.database_name,
                        step.step_code,
                    )
                    continue

                try:
                    await execute_tenant_seed_step(
                        session,
                        request=request,
                        step_code=step.step_code,
                        state=state,
                    )
                except DatabaseError as exc:
                    raise ConflictError(
                        detail="Error aplicando seed tenant en BD dedicada.",
                        internal_code="PROVISIONING_SEED_FAILED",
                    ) from exc
                except ValidationError:
                    raise
                except Exception as exc:
                    raise ConflictError(
                        detail="Error aplicando seed tenant en BD dedicada.",
                        internal_code="PROVISIONING_SEED_FAILED",
                    ) from exc

                await self._record_step_applied(session, step)
                executed.append(step.step_code)
                logger.info(
                    "Tenant seed applied cliente_id=%s database=%s step=%s",
                    request.cliente_id,
                    request.database_name,
                    step.step_code,
                )

            if not state.admin_rol_id or not state.admin_usuario_id or not state.empresa_id:
                raise ConflictError(
                    detail="Seed tenant incompleto — faltan artefactos admin/empresa.",
                    internal_code="PROVISIONING_SEED_INCOMPLETE",
                )

            row_verifications = await self._verify_row_expectations(
                session,
                dedupe_row_expectations(profile.row_expectations),
            )

        return DedicatedTenantSeedResult(
            database_name=request.database_name,
            cliente_id=request.cliente_id,
            plan_suscripcion=profile.plan_suscripcion,
            profile_code=profile.profile_code,
            admin_username=ADMIN_USERNAME,
            admin_usuario_id=state.admin_usuario_id,
            admin_rol_id=state.admin_rol_id,
            empresa_id=state.empresa_id,
            steps_executed=tuple(executed),
            steps_skipped=tuple(skipped),
            row_verifications=row_verifications,
        )

    async def _is_step_applied(
        self,
        session: AsyncSession,
        step: TenantSeedStepDefinition,
    ) -> bool:
        escaped_code = escape_sql_literal(step.marker_code)
        result = await session.execute(
            text(
                f"SELECT checksum_sha256 FROM bootstrap_applied "
                f"WHERE script_code = N'{escaped_code}'"
            )
        )
        row = result.fetchone()
        if row is None:
            return False
        stored = str(row[0] or "")
        if stored.lower() == step.expected_marker_sha256.lower():
            return True
        raise ConflictError(
            detail=f"Marker bootstrap_applied divergente para {step.marker_code}.",
            internal_code="TENANT_SEED_MARKER_CHECKSUM_MISMATCH",
        )

    async def _record_step_applied(
        self,
        session: AsyncSession,
        step: TenantSeedStepDefinition,
    ) -> None:
        escaped_code = escape_sql_literal(step.marker_code)
        escaped_path = escape_sql_literal(f"tenant_seed/{step.step_code}")
        escaped_checksum = escape_sql_literal(step.expected_marker_sha256)
        escaped_step = escape_sql_literal(_STEP_CODE)
        await session.execute(
            text(
                "INSERT INTO bootstrap_applied "
                "(script_code, script_path, checksum_sha256, step_code) "
                f"VALUES (N'{escaped_code}', N'{escaped_path}', "
                f"N'{escaped_checksum}', N'{escaped_step}')"
            )
        )

    async def _verify_row_expectations(
        self,
        session: AsyncSession,
        expectations: tuple[tuple[str, int], ...],
    ) -> tuple[TenantSeedRowVerification, ...]:
        results: list[TenantSeedRowVerification] = []
        for table_name, min_rows in expectations:
            if not _TABLE_NAME_RE.match(table_name):
                raise ValidationError(
                    detail=f"Nombre de tabla tenant seed inválido: {table_name}.",
                    internal_code="INVALID_TENANT_SEED_TABLE_NAME",
                )
            count_result = await session.execute(
                text(f"SELECT COUNT(*) FROM [{table_name}]")
            )
            count = int(count_result.scalar_one() or 0)
            if count < min_rows:
                raise ConflictError(
                    detail=(
                        f"Verificación seed tenant insuficiente en {table_name}: "
                        f"esperado>={min_rows}, actual={count}."
                    ),
                    internal_code="TENANT_SEED_ROW_COUNT_FAILED",
                )
            results.append(
                TenantSeedRowVerification(
                    table_name=table_name,
                    row_count=count,
                    min_rows=min_rows,
                )
            )
        return tuple(results)


__all__ = ["DedicatedTenantSeedService"]
