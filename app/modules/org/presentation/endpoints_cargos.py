# app/modules/org/presentation/endpoints_cargos.py
"""Endpoints ORG - Cargos. Company-scoped: empresa desde sesión JWT (Etapa B)."""
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from uuid import UUID
from typing import Optional

from app.core.authorization.rbac import require_permission
from app.core.exceptions import AuthorizationError, CustomException, NotFoundError
from app.shared.pagination import erp_sort_params, ErpSortParams
from app.modules.org.presentation.org_deps import (
    get_org_session_client_id,
    reject_legacy_empresa_query,
)
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.org.presentation.schemas import CargoCreate, CargoUpdate, CargoRead
from app.modules.org.application.services import cargo_service

router = APIRouter()


@router.get("", response_model=list[CargoRead], summary="Listar cargos")
async def listar_cargos(
    solo_activos: bool = True,
    buscar: Optional[str] = Query(None),
    sort: ErpSortParams = Depends(erp_sort_params),
    _: None = Depends(reject_legacy_empresa_query),
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.cargo.leer")),
    client_id: UUID = Depends(get_org_session_client_id),
):
    return await cargo_service.list_cargos_servicio(
        client_id=client_id,
        solo_activos=solo_activos,
        buscar=buscar,
        sort=sort,
    )


@router.post(
    "/{cargo_id}/reactivar",
    response_model=CargoRead,
    summary="Reactivar cargo",
)
async def reactivar_cargo(
    cargo_id: UUID,
    _: None = Depends(reject_legacy_empresa_query),
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.cargo.actualizar")),
    client_id: UUID = Depends(get_org_session_client_id),
):
    try:
        return await cargo_service.reactivar_cargo_servicio(
            client_id=client_id,
            cargo_id=cargo_id,
        )
    except (NotFoundError, CustomException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e


@router.get("/{cargo_id}", response_model=CargoRead, summary="Detalle cargo")
async def detalle_cargo(
    cargo_id: UUID,
    _: None = Depends(reject_legacy_empresa_query),
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.cargo.leer")),
    client_id: UUID = Depends(get_org_session_client_id),
):
    try:
        return await cargo_service.get_cargo_servicio(
            client_id=client_id,
            cargo_id=cargo_id,
        )
    except (NotFoundError, CustomException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e


@router.post("", response_model=CargoRead, status_code=201, summary="Crear cargo")
async def crear_cargo(
    data: CargoCreate,
    _: None = Depends(reject_legacy_empresa_query),
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.cargo.crear")),
    client_id: UUID = Depends(get_org_session_client_id),
):
    try:
        return await cargo_service.create_cargo_servicio(client_id=client_id, data=data)
    except (AuthorizationError, CustomException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e


@router.put("/{cargo_id}", response_model=CargoRead, summary="Actualizar cargo")
async def actualizar_cargo(
    cargo_id: UUID,
    data: CargoUpdate = Body(...),
    _: None = Depends(reject_legacy_empresa_query),
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.cargo.actualizar")),
    client_id: UUID = Depends(get_org_session_client_id),
):
    try:
        return await cargo_service.update_cargo_servicio(
            client_id=client_id,
            cargo_id=cargo_id,
            data=data,
        )
    except (NotFoundError, CustomException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e


@router.delete(
    "/{cargo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar (baja lógica) cargo",
)
async def eliminar_cargo(
    cargo_id: UUID,
    _: None = Depends(reject_legacy_empresa_query),
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.cargo.eliminar")),
    client_id: UUID = Depends(get_org_session_client_id),
):
    try:
        await cargo_service.delete_cargo_servicio(
            client_id=client_id,
            cargo_id=cargo_id,
        )
    except (NotFoundError, CustomException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e
