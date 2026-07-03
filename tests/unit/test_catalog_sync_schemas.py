"""Tests unitarios — schemas Catalog Sync (F14-BE-UX-01)."""
from uuid import UUID

from app.core.catalog.catalog_sync_types import (
    CatalogSyncBatchResult,
    CatalogSyncBatchStatus,
    CatalogSyncCounts,
    CatalogSyncResult,
    CatalogSyncStatus,
    CatalogSyncTenantOutcome,
)
from app.modules.superadmin.presentation.schemas_catalog_sync import (
    build_catalog_sync_batch_response,
    build_catalog_sync_response,
    build_catalog_sync_tenant_result,
)

_CLIENTE_ID = UUID("3fa85f64-5717-4562-b3fc-2c963f66afa6")


def test_build_catalog_sync_response_includes_tenant_metadata():
    result = CatalogSyncResult(
        catalog="moneda",
        cliente_id=_CLIENTE_ID,
        database_name="erp_cli016",
        status=CatalogSyncStatus.COMPLETED,
        codigo_cliente="CLI016",
        razon_social="Raintex SAC",
        counts=CatalogSyncCounts(inserted=2),
        duration_ms=100,
    )

    response = build_catalog_sync_response("monedas", result)

    assert response.catalogo == "monedas"
    assert response.cliente_id == _CLIENTE_ID
    assert response.codigo_cliente == "CLI016"
    assert response.razon_social == "Raintex SAC"
    assert response.database_name == "erp_cli016"
    assert response.status == "completed"
    assert response.inserted == 2


def test_build_catalog_sync_tenant_result_includes_razon_social():
    outcome = CatalogSyncTenantOutcome(
        cliente_id=_CLIENTE_ID,
        codigo_cliente="CLI016",
        database_name="erp_cli016",
        razon_social="Raintex SAC",
        status=CatalogSyncStatus.COMPLETED,
        counts=CatalogSyncCounts(inserted=1),
        duration_ms=50,
    )

    tenant_result = build_catalog_sync_tenant_result(outcome)

    assert tenant_result.codigo_cliente == "CLI016"
    assert tenant_result.razon_social == "Raintex SAC"
    assert tenant_result.status == "completed"


def test_build_catalog_sync_batch_response_propagates_razon_social_in_results():
    outcome = CatalogSyncTenantOutcome(
        cliente_id=_CLIENTE_ID,
        codigo_cliente="CLI016",
        database_name="erp_cli016",
        razon_social="Raintex SAC",
        status=CatalogSyncStatus.COMPLETED,
        counts=CatalogSyncCounts(inserted=3),
        duration_ms=75,
    )
    batch = CatalogSyncBatchResult(
        catalog="moneda",
        status=CatalogSyncBatchStatus.COMPLETED,
        tenants_total=1,
        tenants_completed=1,
        aggregated_counts=CatalogSyncCounts(inserted=3),
        outcomes=(outcome,),
        duration_ms=200,
    )

    response = build_catalog_sync_batch_response("monedas", batch)

    assert len(response.results) == 1
    assert response.results[0].razon_social == "Raintex SAC"
    assert response.results[0].codigo_cliente == "CLI016"
