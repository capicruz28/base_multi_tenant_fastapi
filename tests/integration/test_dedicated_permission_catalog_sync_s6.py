"""F12-B — integración S6 → S6b (permission catalog sync) → S7 wiring."""
from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.infrastructure.provisioning.dedicated_catalog_seed_service import (
    DedicatedCatalogSeedService,
)
from app.infrastructure.provisioning.dedicated_catalog_seed_types import (
    DedicatedCatalogSeedRequest,
)
from app.infrastructure.provisioning.dedicated_permission_catalog_sync_types import (
    DedicatedPermissionCatalogSyncResult,
)
from app.infrastructure.provisioning.dedicated_tenant_seed_service import (
    DedicatedTenantSeedService,
)
from tests.unit.test_f4_06_dedicated_catalog_seed_service import (
    MockCatalogDdlClient,
    _patch_catalog_checksums,
)

CLIENTE_ID = uuid4()


class MockPermissionCatalogSyncService:
    def __init__(self) -> None:
        self.calls: list = []
        self.run_sync = AsyncMock(side_effect=self._run_sync)

    async def _run_sync(self, request, **kwargs):
        self.calls.append((request, kwargs))
        return DedicatedPermissionCatalogSyncResult(
            database_name=request.database_name,
            cliente_id=request.cliente_id,
            status="applied",
            registry_hash="abc123" * 8,
            inserted=9,
            updated=2,
            deactivated=1,
            declared_count=11,
        )


@pytest.fixture(autouse=True)
def enable_permission_catalog_sync(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        "app.core.config.settings.DEDICATED_PERMISSION_CATALOG_SYNC_ENABLED",
        True,
    )


@pytest.fixture
def ddl_client() -> MockCatalogDdlClient:
    return MockCatalogDdlClient()


@pytest.fixture
def sync_service() -> MockPermissionCatalogSyncService:
    return MockPermissionCatalogSyncService()


@pytest.fixture
def catalog_service(
    tmp_path,
    ddl_client: MockCatalogDdlClient,
    sync_service: MockPermissionCatalogSyncService,
    monkeypatch: pytest.MonkeyPatch,
):
    _patch_catalog_checksums(tmp_path, monkeypatch)
    return DedicatedCatalogSeedService(
        ddl_client=ddl_client,
        bootstrap_root=tmp_path,
        permission_catalog_sync=sync_service,
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_s6_catalog_seed_invokes_s6b_permission_sync_after_sql_scripts(
    catalog_service: DedicatedCatalogSeedService,
    sync_service: MockPermissionCatalogSyncService,
):
    request = DedicatedCatalogSeedRequest(
        database_name="erp_acme001",
        cliente_id=CLIENTE_ID,
        plan_suscripcion="trial",
        provisioning_run_id=uuid4(),
    )
    result = await catalog_service.run_catalog_seed(request)

    assert result.scripts_executed == (
        "catalog_s010",
        "catalog_s020",
        "catalog_s030",
        "catalog_s040",
        "catalog_s041",
        "catalog_s042",
    )
    assert result.permission_catalog_sync_status == "applied"
    assert result.permission_catalog_sync_registry_hash == "abc123" * 8
    assert result.permission_catalog_sync_inserted == 9
    assert len(sync_service.calls) == 1
    sync_request = sync_service.calls[0][0]
    assert sync_request.database_name == "erp_acme001"
    assert sync_request.cliente_id == CLIENTE_ID


@pytest.mark.integration
@pytest.mark.asyncio
async def test_s6b_runs_before_s7_tenant_seed_in_orchestrator_order():
    """Verifica orden de pasos saga: apply_catalogs (S6+S6b) precede seed_tenant (S7)."""
    from app.modules.tenant.application.provisioning.provisioning_step_code import (
        ProvisioningStepCode,
    )

    ordered = [
        ProvisioningStepCode.APPLY_CATALOGS.value,
        ProvisioningStepCode.SEED_TENANT.value,
    ]
    assert ordered.index("apply_catalogs") < ordered.index("seed_tenant")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_s7_tenant_seed_service_does_not_own_permission_catalog_sync():
    """S7 no invoca permission catalog sync — responsabilidad exclusiva de S6."""
    tenant_seed = DedicatedTenantSeedService()
    assert not hasattr(tenant_seed, "run_permission_catalog_sync")
