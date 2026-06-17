# app/modules/org/presentation/endpoints_centros_costo.py
"""Endpoints ORG - Centros de costo. Company-scoped: empresa desde sesión JWT (Etapa B)."""
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from uuid import UUID
from typing import Optional, Union

from app.core.authorization.rbac import require_permission
from app.core.exceptions import AuthorizationError, CustomException, NotFoundError
from app.shared.pagination import erp_pagination_params, erp_sort_params, ErpPaginationParams, ErpSortParams
from app.modules.org.presentation.org_deps import (
    get_org_session_client_id,
    reject_legacy_empresa_query,
)
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.org.presentation.schemas import (
    CentroCostoCreate,
    CentroCostoUpdate,
    CentroCostoRead,
    PaginatedCentroCostoResponse,
)
from app.modules.org.application.services import centro_costo_service

router = APIRouter()


@router.get(
    "",
    response_model=Union[list[CentroCostoRead], PaginatedCentroCostoResponse],
    summary="Listar centros de costo",
)
async def listar_centros_costo(
    solo_activos: bool = True,
    buscar: Optional[str] = Query(None, description="Búsqueda por código o nombre"),
    pagination: ErpPaginationParams = Depends(erp_pagination_params),
    sort: ErpSortParams = Depends(erp_sort_params),
    _: None = Depends(reject_legacy_empresa_query),
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.centro_costo.leer")),
    client_id: UUID = Depends(get_org_session_client_id),
):
    return await centro_costo_service.list_centros_costo_servicio(
        client_id=client_id,
        solo_activos=solo_activos,
        buscar=buscar,
        pagination=pagination,
        sort=sort,
    )


@router.post(
    "/{centro_costo_id}/reactivar",
    response_model=CentroCostoRead,
    summary="Reactivar centro de costo",
)
async def reactivar_centro_costo(
    centro_costo_id: UUID,
    _: None = Depends(reject_legacy_empresa_query),
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.centro_costo.actualizar")),
    client_id: UUID = Depends(get_org_session_client_id),
):
    try:
        return await centro_costo_service.reactivar_centro_costo_servicio(
            client_id=client_id,
            centro_costo_id=centro_costo_id,
        )
    except (NotFoundError, CustomException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e


@router.get("/{centro_costo_id}", response_model=CentroCostoRead, summary="Detalle centro de costo")
async def detalle_centro_costo(
    centro_costo_id: UUID,
    _: None = Depends(reject_legacy_empresa_query),
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.centro_costo.leer")),
    client_id: UUID = Depends(get_org_session_client_id),
):
    try:
        return await centro_costo_service.get_centro_costo_servicio(
            client_id=client_id,
            centro_costo_id=centro_costo_id,
        )
    except (NotFoundError, CustomException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e


@router.post("", response_model=CentroCostoRead, status_code=201, summary="Crear centro de costo")
async def crear_centro_costo(
    data: CentroCostoCreate,
    _: None = Depends(reject_legacy_empresa_query),
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.centro_costo.crear")),
    client_id: UUID = Depends(get_org_session_client_id),
):
    try:
        return await centro_costo_service.create_centro_costo_servicio(
            client_id=client_id, data=data
        )
    except (AuthorizationError, CustomException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e


@router.put("/{centro_costo_id}", response_model=CentroCostoRead, summary="Actualizar centro de costo")
async def actualizar_centro_costo(
    centro_costo_id: UUID,
    data: CentroCostoUpdate = Body(...),
    _: None = Depends(reject_legacy_empresa_query),
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.centro_costo.actualizar")),
    client_id: UUID = Depends(get_org_session_client_id),
):
    try:
        return await centro_costo_service.update_centro_costo_servicio(
            client_id=client_id,
            centro_costo_id=centro_costo_id,
            data=data,
        )
    except (NotFoundError, CustomException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e


@router.delete(
    "/{centro_costo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar (baja lógica) centro de costo",
)
async def eliminar_centro_costo(
    centro_costo_id: UUID,
    _: None = Depends(reject_legacy_empresa_query),
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.centro_costo.eliminar")),
    client_id: UUID = Depends(get_org_session_client_id),
):
    try:
        await centro_costo_service.delete_centro_costo_servicio(
            client_id=client_id,
            centro_costo_id=centro_costo_id,
        )
    except (NotFoundError, CustomException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e
