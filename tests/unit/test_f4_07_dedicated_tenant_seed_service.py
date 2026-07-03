"""PR-F4-07 — tests unitarios DedicatedTenantSeedService."""
from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ValidationError
from app.infrastructure.provisioning.dedicated_tenant_seed_service import (
    DedicatedTenantSeedService,
)
from app.infrastructure.provisioning.dedicated_tenant_seed_types import (
    DedicatedTenantSeedRequest,
)
from app.infrastructure.provisioning.tenant_seed_profiles import (
    resolve_tenant_seed_profile,
    validate_tenant_seed_profile_integrity,
)
from app.modules.tenant.application.services.cliente_onboarding_service import (
    SECUENCIAS_CODIGO,
)

CLIENTE_ID = uuid4()
ADMIN_ROL_ID = uuid4()
ADMIN_USER_ID = uuid4()
EMPRESA_ID = uuid4()


def _request() -> DedicatedTenantSeedRequest:
    return DedicatedTenantSeedRequest(
        database_name="erp_acme001",
        cliente_id=CLIENTE_ID,
        codigo_cliente="ACME001",
        subdominio="acme",
        razon_social="ACME S.A.",
        contacto_email="admin@acme.test",
        plan_suscripcion="trial",
    )


class MockResult:
    def __init__(
        self,
        *,
        fetchone_value=None,
        scalar_value: int = 0,
    ) -> None:
        self._fetchone_value = fetchone_value
        self._scalar_value = scalar_value

    def fetchone(self):
        return self._fetchone_value

    def scalar_one(self):
        return self._scalar_value


class MockSession:
    def __init__(self) -> None:
        self.executed: list[str] = []
        self.markers: dict[str, str] = {}
        self.row_counts = {
            "permiso": 1,
            "modulo": 27,
            "rol": 3,
            "org_empresa": 1,
            "usuario": 1,
            "cfg_codigo_secuencia": len(SECUENCIAS_CODIGO),
        }

    async def execute(self, statement, params=None):
        sql = str(statement)
        self.executed.append(sql)

        if "FROM bootstrap_applied" in sql and "script_code" in sql:
            for code, checksum in self.markers.items():
                if f"N'{code}'" in sql:
                    return MockResult(fetchone_value=(checksum,))
            return MockResult(fetchone_value=None)

        if "INSERT INTO bootstrap_applied" in sql:
            for step in (
                "tenant_seed_base_roles_v1",
                "tenant_seed_org_empresa_v1",
                "tenant_seed_admin_user_v1",
                "tenant_seed_admin_empresa_link_v1",
                "tenant_seed_tenant_rbac_v1",
                "tenant_seed_codigo_secuencias_v1",
            ):
                if f"N'{step}'" in sql:
                    parts = sql.split("N'")
                    if len(parts) >= 4:
                        self.markers[step] = parts[3].split("'")[0]
                    break
            return MockResult()

        if "SELECT COUNT(*)" in sql:
            for table, count in self.row_counts.items():
                if f"[{table}]" in sql or f"FROM {table}" in sql:
                    return MockResult(scalar_value=count)
            return MockResult(scalar_value=0)

        if "SELECT TOP 1 rol_id" in sql:
            return MockResult(fetchone_value=(ADMIN_ROL_ID,))
        if "SELECT TOP 1 usuario_id" in sql:
            return MockResult(fetchone_value=(ADMIN_USER_ID,))

        return MockResult()


@pytest.fixture
def mock_session() -> MockSession:
    return MockSession()


@pytest.fixture
def service(mock_session: MockSession) -> DedicatedTenantSeedService:
    @asynccontextmanager
    async def _factory(_database_name: str):
        yield mock_session  # type: ignore[misc]

    return DedicatedTenantSeedService(session_factory=_factory)


@pytest.mark.unit
def test_f4_07_profile_has_ordered_s7_steps():
    profile = resolve_tenant_seed_profile("trial")
    codes = [step.step_code for step in profile.steps]
    assert codes == [
        "seed_base_roles",
        "seed_org_empresa",
        "seed_admin_user",
        "seed_admin_empresa_link",
        "seed_tenant_rbac",
        "seed_codigo_secuencias",
    ]
    validate_tenant_seed_profile_integrity(profile)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_07_run_executes_all_steps(
    service: DedicatedTenantSeedService,
):
    state_updates = []

    async def _fake_step(session, *, request, step_code, state):
        state_updates.append(step_code)
        state.admin_rol_id = ADMIN_ROL_ID
        state.admin_usuario_id = ADMIN_USER_ID
        state.empresa_id = EMPRESA_ID

    with patch(
        "app.infrastructure.provisioning.dedicated_tenant_seed_service.execute_tenant_seed_step",
        side_effect=_fake_step,
    ), patch(
        "app.infrastructure.provisioning.dedicated_tenant_seed_service.verify_tenant_seed_prerequisites",
        new=AsyncMock(),
    ):
        result = await service.run_tenant_seed(_request())

    assert result.steps_executed == (
        "seed_base_roles",
        "seed_org_empresa",
        "seed_admin_user",
        "seed_admin_empresa_link",
        "seed_tenant_rbac",
        "seed_codigo_secuencias",
    )
    assert result.steps_skipped == ()
    assert result.admin_rol_id == ADMIN_ROL_ID
    assert result.empresa_id == EMPRESA_ID
    assert len(state_updates) == 6


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_07_rerun_is_idempotent(
    service: DedicatedTenantSeedService,
    mock_session: MockSession,
):
    profile = resolve_tenant_seed_profile("trial")
    for step in profile.steps:
        mock_session.markers[step.marker_code] = step.expected_marker_sha256

    with patch(
        "app.infrastructure.provisioning.dedicated_tenant_seed_service.execute_tenant_seed_step",
        new=AsyncMock(),
    ) as mocked_step, patch(
        "app.infrastructure.provisioning.dedicated_tenant_seed_service.hydrate_tenant_seed_state",
        new=AsyncMock(),
    ) as mocked_hydrate, patch(
        "app.infrastructure.provisioning.dedicated_tenant_seed_service.verify_tenant_seed_prerequisites",
        new=AsyncMock(),
    ):

        async def _hydrate(session, *, request, state, step_code):
            state.admin_rol_id = ADMIN_ROL_ID
            state.admin_usuario_id = ADMIN_USER_ID
            state.empresa_id = EMPRESA_ID

        mocked_hydrate.side_effect = _hydrate

        result = await service.run_tenant_seed(_request())

    assert result.steps_executed == ()
    assert len(result.steps_skipped) == 6
    mocked_step.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_07_marker_checksum_mismatch_raises_conflict(
    service: DedicatedTenantSeedService,
    mock_session: MockSession,
):
    mock_session.markers["tenant_seed_base_roles_v1"] = "deadbeef" * 8

    with patch(
        "app.infrastructure.provisioning.dedicated_tenant_seed_service.verify_tenant_seed_prerequisites",
        new=AsyncMock(),
    ):
        with pytest.raises(ConflictError) as exc:
            await service.run_tenant_seed(_request())
    assert exc.value.internal_code == "TENANT_SEED_MARKER_CHECKSUM_MISMATCH"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_07_catalog_prerequisite_failure(
    service: DedicatedTenantSeedService,
    mock_session: MockSession,
):
    mock_session.row_counts["modulo"] = 0

    with pytest.raises(ConflictError) as exc:
        await service.run_tenant_seed(_request())
    assert exc.value.internal_code == "TENANT_SEED_CATALOG_PREREQ_FAILED"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_07_row_count_failure():
    @asynccontextmanager
    async def _factory_with_bad_counts(_database_name: str):
        session = MockSession()
        session.row_counts["org_empresa"] = 0
        yield session  # type: ignore[misc]

    broken = DedicatedTenantSeedService(session_factory=_factory_with_bad_counts)

    async def _fake_step(session, *, request, step_code, state):
        state.admin_rol_id = ADMIN_ROL_ID
        state.admin_usuario_id = ADMIN_USER_ID
        state.empresa_id = EMPRESA_ID

    with patch(
        "app.infrastructure.provisioning.dedicated_tenant_seed_service.execute_tenant_seed_step",
        side_effect=_fake_step,
    ), patch(
        "app.infrastructure.provisioning.dedicated_tenant_seed_service.verify_tenant_seed_prerequisites",
        new=AsyncMock(),
    ):
        with pytest.raises(ConflictError) as exc:
            await broken.run_tenant_seed(_request())
    assert exc.value.internal_code == "TENANT_SEED_ROW_COUNT_FAILED"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_07_default_session_disabled_without_factory():
    service = DedicatedTenantSeedService()
    with pytest.raises(ValidationError) as exc:
        await service.run_tenant_seed(_request())
    assert exc.value.internal_code == "PROVISIONING_DDL_EXECUTOR_DISABLED"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_07_step_failure_maps_to_provisioning_seed_failed(
    service: DedicatedTenantSeedService,
):
    with patch(
        "app.infrastructure.provisioning.dedicated_tenant_seed_service.verify_tenant_seed_prerequisites",
        new=AsyncMock(),
    ), patch(
        "app.infrastructure.provisioning.dedicated_tenant_seed_service.execute_tenant_seed_step",
        side_effect=RuntimeError("boom"),
    ):
        with pytest.raises(ConflictError) as exc:
            await service.run_tenant_seed(_request())
    assert exc.value.internal_code == "PROVISIONING_SEED_FAILED"
