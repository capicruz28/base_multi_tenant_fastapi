# app/modules/org/presentation/endpoints_sucursales.py
"""Endpoints ORG - Sucursales. Company-scoped: empresa desde sesión JWT (Etapa B)."""
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
from app.modules.org.presentation.schemas import SucursalCreate, SucursalUpdate, SucursalRead
from app.modules.org.application.services import sucursal_service

router = APIRouter()


@router.get("", response_model=list[SucursalRead], summary="Listar sucursales")
async def listar_sucursales(
    solo_activos: bool = True,
    buscar: Optional[str] = Query(None),
    sort: ErpSortParams = Depends(erp_sort_params),
    _: None = Depends(reject_legacy_empresa_query),
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.sucursal.leer")),
    client_id: UUID = Depends(get_org_session_client_id),
):
    """Lista sucursales de la empresa activa en sesión."""
    return await sucursal_service.list_sucursales_servicio(
        client_id=client_id,
        solo_activos=solo_activos,
        buscar=buscar,
        sort=sort,
    )


@router.post(
    "/{sucursal_id}/reactivar",
    response_model=SucursalRead,
    summary="Reactivar sucursal",
)
async def reactivar_sucursal(
    sucursal_id: UUID,
    _: None = Depends(reject_legacy_empresa_query),
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.sucursal.actualizar")),
    client_id: UUID = Depends(get_org_session_client_id),
):
    """Marca la sucursal como activa (es_activo = True) en la empresa de sesión."""
    try:
        return await sucursal_service.reactivar_sucursal_servicio(
            client_id=client_id,
            sucursal_id=sucursal_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e
    except CustomException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e


@router.get("/{sucursal_id}", response_model=SucursalRead, summary="Detalle sucursal")
async def detalle_sucursal(
    sucursal_id: UUID,
    _: None = Depends(reject_legacy_empresa_query),
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.sucursal.leer")),
    client_id: UUID = Depends(get_org_session_client_id),
):
    """Detalle de una sucursal de la empresa activa."""
    try:
        return await sucursal_service.get_sucursal_servicio(
            client_id=client_id,
            sucursal_id=sucursal_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e
    except CustomException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e


@router.post("", response_model=SucursalRead, status_code=201, summary="Crear sucursal")
async def crear_sucursal(
    data: SucursalCreate,
    _: None = Depends(reject_legacy_empresa_query),
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.sucursal.crear")),
    client_id: UUID = Depends(get_org_session_client_id),
):
    """Crea una sucursal. empresa_id del body debe coincidir con la sesión."""
    try:
        return await sucursal_service.create_sucursal_servicio(client_id=client_id, data=data)
    except AuthorizationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e
    except CustomException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e


@router.put("/{sucursal_id}", response_model=SucursalRead, summary="Actualizar sucursal")
async def actualizar_sucursal(
    sucursal_id: UUID,
    data: SucursalUpdate = Body(...),
    _: None = Depends(reject_legacy_empresa_query),
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.sucursal.actualizar")),
    client_id: UUID = Depends(get_org_session_client_id),
):
    """Actualiza una sucursal de la empresa activa."""
    try:
        return await sucursal_service.update_sucursal_servicio(
            client_id=client_id,
            sucursal_id=sucursal_id,
            data=data,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e
    except CustomException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e


@router.delete(
    "/{sucursal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar (baja lógica) sucursal",
)
async def eliminar_sucursal(
    sucursal_id: UUID,
    _: None = Depends(reject_legacy_empresa_query),
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.sucursal.eliminar")),
    client_id: UUID = Depends(get_org_session_client_id),
):
    """Marca una sucursal como inactiva (baja lógica) en la empresa de sesión."""
    try:
        await sucursal_service.delete_sucursal_servicio(
            client_id=client_id,
            sucursal_id=sucursal_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e
    except CustomException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e
