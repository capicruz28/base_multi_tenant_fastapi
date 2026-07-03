from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.catalog.catalog_sync_definitions import CatalogKind
from app.core.catalog.catalog_sync_types import (
    CatalogSyncBatchResult,
    CatalogSyncErrorDetail,
    CatalogSyncResult,
    CatalogSyncTenantOutcome,
)

CATALOG_SLUG_TO_KIND: dict[str, CatalogKind] = {
    "monedas": CatalogKind.MONEDA,
    "paises": CatalogKind.PAIS,
    "departamentos": CatalogKind.DEPARTAMENTO,
    "provincias": CatalogKind.PROVINCIA,
    "distritos": CatalogKind.DISTRITO,
}

class CatalogSyncErrorItem(BaseModel):
    internal_code: str = Field(..., description="Código interno del error")
    message: str = Field(..., description="Mensaje legible del error")
    details: Optional[dict] = Field(None, description="Detalle estructurado opcional")


class CatalogSyncCounts(BaseModel):
    inserted: int = Field(0, ge=0, description="Filas insertadas con PK Platform")
    updated: int = Field(0, ge=0, description="Filas actualizadas por diff")
    skipped: int = Field(0, ge=0, description="Filas idénticas sin mutación")
    deactivated: int = Field(0, ge=0, description="Filas desactivadas (soft delete)")
    platform_total: int = Field(0, ge=0, description="Total filas leídas de Platform")
    dedicated_before: int = Field(0, ge=0, description="Filas en dedicated antes del sync")


class CatalogSyncResponse(BaseModel):
    catalogo: str = Field(..., description="Slug del catálogo sincronizado")
    cliente_id: UUID = Field(..., description="Tenant dedicated objetivo")
    codigo_cliente: str = Field(..., description="Código del tenant")
    razon_social: str = Field(..., description="Razón social del tenant")
    database_name: str = Field(..., description="Nombre de la BD dedicada")
    status: str = Field(..., description="completed | failed")
    inserted: int = Field(0, ge=0)
    updated: int = Field(0, ge=0)
    deactivated: int = Field(0, ge=0)
    skipped: int = Field(0, ge=0)
    duration_ms: int = Field(..., ge=0, description="Duración de la operación en ms")
    errors: List[CatalogSyncErrorItem] = Field(
        default_factory=list,
        description="Errores de sincronización (vacío si status=completed)",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "catalogo": "monedas",
                    "cliente_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                    "codigo_cliente": "CLI016",
                    "razon_social": "Raintex SAC",
                    "database_name": "erp_cli016",
                    "status": "completed",
                    "inserted": 5,
                    "updated": 0,
                    "deactivated": 0,
                    "skipped": 0,
                    "duration_ms": 312,
                    "errors": [],
                }
            ]
        }
    }


class CatalogSyncTenantResult(BaseModel):
    cliente_id: UUID
    codigo_cliente: str
    razon_social: str = Field(..., description="Razón social del tenant")
    database_name: str
    status: str = Field(..., description="completed | failed")
    inserted: int = Field(0, ge=0)
    updated: int = Field(0, ge=0)
    deactivated: int = Field(0, ge=0)
    skipped: int = Field(0, ge=0)
    duration_ms: int = Field(..., ge=0)
    errors: List[CatalogSyncErrorItem] = Field(default_factory=list)


class CatalogSyncBatchResponse(BaseModel):
    catalogo: str = Field(..., description="Slug del catálogo sincronizado")
    status: str = Field(..., description="completed | partial | failed")
    tenants_total: int = Field(..., ge=0)
    completed: int = Field(..., ge=0, description="Tenants sincronizados exitosamente")
    failed: int = Field(..., ge=0, description="Tenants con error")
    inserted: int = Field(0, ge=0)
    updated: int = Field(0, ge=0)
    deactivated: int = Field(0, ge=0)
    skipped: int = Field(0, ge=0)
    duration_ms: int = Field(..., ge=0)
    results: List[CatalogSyncTenantResult] = Field(default_factory=list)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "catalogo": "monedas",
                    "status": "completed",
                    "tenants_total": 2,
                    "completed": 2,
                    "failed": 0,
                    "inserted": 10,
                    "updated": 0,
                    "deactivated": 0,
                    "skipped": 0,
                    "duration_ms": 890,
                    "results": [
                        {
                            "cliente_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                            "codigo_cliente": "CLI016",
                            "razon_social": "Raintex SAC",
                            "database_name": "erp_cli016",
                            "status": "completed",
                            "inserted": 5,
                            "updated": 0,
                            "deactivated": 0,
                            "skipped": 0,
                            "duration_ms": 312,
                            "errors": [],
                        }
                    ],
                }
            ]
        }
    }


def _error_item_from_detail(error: CatalogSyncErrorDetail | None) -> List[CatalogSyncErrorItem]:
    if error is None:
        return []
    return [
        CatalogSyncErrorItem(
            internal_code=error.internal_code,
            message=error.message,
            details=error.details,
        )
    ]


def _counts_from_result(counts) -> tuple[int, int, int, int]:
    if counts is None:
        return 0, 0, 0, 0
    return counts.inserted, counts.updated, counts.deactivated, counts.skipped


def build_catalog_sync_response(
    catalogo_slug: str,
    result: CatalogSyncResult,
) -> CatalogSyncResponse:
    inserted, updated, deactivated, skipped = _counts_from_result(result.counts)
    return CatalogSyncResponse(
        catalogo=catalogo_slug,
        cliente_id=result.cliente_id,
        codigo_cliente=result.codigo_cliente,
        razon_social=result.razon_social,
        database_name=result.database_name,
        status=result.status.value,
        inserted=inserted,
        updated=updated,
        deactivated=deactivated,
        skipped=skipped,
        duration_ms=result.duration_ms,
        errors=_error_item_from_detail(result.error),
    )


def build_catalog_sync_tenant_result(outcome: CatalogSyncTenantOutcome) -> CatalogSyncTenantResult:
    inserted, updated, deactivated, skipped = _counts_from_result(outcome.counts)
    return CatalogSyncTenantResult(
        cliente_id=outcome.cliente_id,
        codigo_cliente=outcome.codigo_cliente,
        razon_social=outcome.razon_social,
        database_name=outcome.database_name,
        status=outcome.status.value,
        inserted=inserted,
        updated=updated,
        deactivated=deactivated,
        skipped=skipped,
        duration_ms=outcome.duration_ms,
        errors=_error_item_from_detail(outcome.error),
    )


def build_catalog_sync_batch_response(
    catalogo_slug: str,
    result: CatalogSyncBatchResult,
) -> CatalogSyncBatchResponse:
    agg = result.aggregated_counts
    return CatalogSyncBatchResponse(
        catalogo=catalogo_slug,
        status=result.status.value,
        tenants_total=result.tenants_total,
        completed=result.tenants_completed,
        failed=result.tenants_failed,
        inserted=agg.inserted,
        updated=agg.updated,
        deactivated=agg.deactivated,
        skipped=agg.skipped,
        duration_ms=result.duration_ms,
        results=[build_catalog_sync_tenant_result(item) for item in result.outcomes],
    )
