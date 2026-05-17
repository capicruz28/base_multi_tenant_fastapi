# app/modules/org/presentation/endpoints_centros_costo.py
"""Endpoints ORG - Centros de costo. client_id desde current_user.cliente_id."""
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from uuid import UUID
from typing import Optional

from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.org.presentation.schemas import (
    CentroCostoCreate,
    CentroCostoUpdate,
    CentroCostoRead,
)
from app.modules.org.application.services import centro_costo_service
from app.core.exceptions import NotFoundError

router = APIRouter()

@router.get("", response_model=list[CentroCostoRead], summary="Listar centros de costo")
async def listar_centros_costo(
    empresa_id: Optional[UUID] = Query(None),
    solo_activos: bool = True,
    buscar: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.centro_costo.leer")),
):
    client_id = current_user.cliente_id
    return await centro_costo_service.list_centros_costo_servicio(
        client_id=client_id,
        empresa_id=empresa_id,
        solo_activos=solo_activos,
        buscar=buscar,
    )


@router.post(
    "/{centro_costo_id}/reactivar",
    response_model=CentroCostoRead,
    summary="Reactivar centro de costo",
)
async def reactivar_centro_costo(
    centro_costo_id: UUID,
    empresa_id: UUID = Query(..., description="Empresa propietaria del centro de costo."),
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.centro_costo.actualizar")),
):
    """Marca el centro de costo como activo (es_activo = True) dentro del tenant."""
    client_id = current_user.cliente_id
    try:
        return await centro_costo_service.reactivar_centro_costo_servicio(
            client_id=client_id,
            centro_costo_id=centro_costo_id,
            empresa_id=empresa_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.get("/{centro_costo_id}", response_model=CentroCostoRead, summary="Detalle centro de costo")
async def detalle_centro_costo(
    centro_costo_id: UUID,
    empresa_id: UUID = Query(..., description="Empresa propietaria del centro de costo."),
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.centro_costo.leer")),
):
    client_id = current_user.cliente_id
    try:
        return await centro_costo_service.get_centro_costo_servicio(
            client_id=client_id,
            centro_costo_id=centro_costo_id,
            empresa_id=empresa_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("", response_model=CentroCostoRead, status_code=201, summary="Crear centro de costo")
async def crear_centro_costo(
    data: CentroCostoCreate,
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.centro_costo.crear")),
):
    client_id = current_user.cliente_id
    return await centro_costo_service.create_centro_costo_servicio(
        client_id=client_id,
        data=data,
    )


@router.put("/{centro_costo_id}", response_model=CentroCostoRead, summary="Actualizar centro de costo")
async def actualizar_centro_costo(
    centro_costo_id: UUID,
    empresa_id: UUID = Query(..., description="Empresa propietaria del centro de costo."),
    data: CentroCostoUpdate = Body(...),
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.centro_costo.actualizar")),
):
    client_id = current_user.cliente_id
    try:
        return await centro_costo_service.update_centro_costo_servicio(
            client_id=client_id,
            centro_costo_id=centro_costo_id,
            data=data,
            empresa_id=empresa_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.delete(
    "/{centro_costo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar (baja lógica) centro de costo",
)
async def eliminar_centro_costo(
    centro_costo_id: UUID,
    empresa_id: UUID = Query(..., description="Empresa propietaria del centro de costo."),
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.centro_costo.eliminar")),
):
    """Marca un centro de costo como inactivo (baja lógica) dentro del tenant."""
    client_id = current_user.cliente_id
    try:
        await centro_costo_service.delete_centro_costo_servicio(
            client_id=client_id,
            centro_costo_id=centro_costo_id,
            empresa_id=empresa_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
