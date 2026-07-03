from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, status

from app.api.deps import get_current_active_user
from app.core.authorization.lbac import require_super_admin
from app.core.catalog.catalog_sync_definitions import CatalogKind
from app.core.exceptions import ServiceError
from app.modules.superadmin.application.services.catalog_sync_orchestrator import (
    CatalogSyncOrchestrator,
)
from app.modules.superadmin.presentation.schemas_catalog_sync import (
    CATALOG_SLUG_TO_KIND,
    CatalogSyncBatchResponse,
    CatalogSyncResponse,
    build_catalog_sync_batch_response,
    build_catalog_sync_response,
)

router = APIRouter()

_orchestrator = CatalogSyncOrchestrator()

_SUPPORTED_CATALOGS = ", ".join(sorted(CATALOG_SLUG_TO_KIND))


def _resolve_catalog_kind(catalogo: str) -> CatalogKind:
    kind = CATALOG_SLUG_TO_KIND.get(catalogo.strip().lower())
    if kind is None:
        raise ServiceError(
            status_code=422,
            detail=(
                f"Catálogo no soportado: '{catalogo}'. "
                f"Valores permitidos: {_SUPPORTED_CATALOGS}."
            ),
            internal_code="CATALOG_NOT_SUPPORTED",
        )
    return kind


@router.post(
    "/sync/{catalogo}/{cliente_id}",
    response_model=CatalogSyncResponse,
    status_code=status.HTTP_200_OK,
    summary="Sincronizar catálogo hacia un tenant Dedicated",
    description=(
        "Replica manualmente un catálogo Product Reference desde Platform (BD ERP shared) "
        "hacia la BD dedicada de un único cliente. Preserva UUID Platform en INSERT. "
        "Catálogos soportados: monedas, paises, departamentos, provincias, distritos."
    ),
    operation_id="sync_catalogo_dedicated_cliente",
    responses={
        200: {
            "description": "Sincronización ejecutada (completed o failed en el body)",
            "content": {
                "application/json": {
                    "example": {
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
                }
            },
        },
        403: {"description": "Requiere Super Administrador"},
        404: {"description": "Cliente no encontrado"},
        422: {
            "description": "Validación pre-sync (cliente no dedicated, FK prerequisito, catálogo inválido)",
        },
        503: {"description": "BD dedicada no alcanzable"},
    },
    tags=["Catálogos Globales (Super Admin)"],
)
@require_super_admin()
async def sync_catalogo_dedicated_cliente(
    catalogo: str = Path(
        ...,
        description="Slug del catálogo: monedas | paises | departamentos | provincias | distritos",
    ),
    cliente_id: UUID = Path(..., description="UUID del tenant dedicated objetivo"),
    current_user=Depends(get_current_active_user),
):
    catalogo_slug = catalogo.strip().lower()
    kind = _resolve_catalog_kind(catalogo_slug)
    result = await _orchestrator.sync_one(cliente_id, kind)
    return build_catalog_sync_response(catalogo_slug, result)


@router.post(
    "/sync/{catalogo}",
    response_model=CatalogSyncBatchResponse,
    status_code=status.HTTP_200_OK,
    summary="Sincronizar catálogo hacia todos los tenants Dedicated",
    description=(
        "Replica manualmente un catálogo Product Reference hacia cada tenant dedicated activo "
        "con conexión principal. Reutiliza el mismo motor que la sincronización individual. "
        "Con continue_on_error=false detiene el batch al primer error."
    ),
    operation_id="sync_catalogo_all_dedicated",
    responses={
        200: {
            "description": "Batch completado (completed, partial o failed en el body)",
            "content": {
                "application/json": {
                    "example": {
                        "catalogo": "monedas",
                        "status": "partial",
                        "tenants_total": 3,
                        "completed": 2,
                        "failed": 1,
                        "inserted": 10,
                        "updated": 0,
                        "deactivated": 0,
                        "skipped": 0,
                        "duration_ms": 2100,
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
                }
            },
        },
        403: {"description": "Requiere Super Administrador"},
        422: {"description": "Catálogo no soportado"},
    },
    tags=["Catálogos Globales (Super Admin)"],
)
@require_super_admin()
async def sync_catalogo_all_dedicated(
    catalogo: str = Path(
        ...,
        description="Slug del catálogo: monedas | paises | departamentos | provincias | distritos",
    ),
    continue_on_error: bool = Query(
        True,
        description="Si es false, detiene el batch al primer tenant con error",
    ),
    current_user=Depends(get_current_active_user),
):
    catalogo_slug = catalogo.strip().lower()
    kind = _resolve_catalog_kind(catalogo_slug)
    result = await _orchestrator.sync_all(kind, continue_on_error=continue_on_error)
    return build_catalog_sync_batch_response(catalogo_slug, result)
