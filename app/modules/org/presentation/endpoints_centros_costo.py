# app/modules/org/presentation/endpoints_centros_costo.py
"""Endpoints ORG - Centros de costo. client_id desde current_user.cliente_id."""
from fastapi import APIRouter, Depends, HTTPException, Query
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
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.area.leer")),
):
    client_id = current_user.cliente_id
    return await centro_costo_service.list_centros_costo_servicio(
        client_id=client_id,
        empresa_id=empresa_id,
        solo_activos=solo_activos,
    )


@router.get("/{centro_costo_id}", response_model=CentroCostoRead, summary="Detalle centro de costo")
async def detalle_centro_costo(
    centro_costo_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.area.leer")),
):
    client_id = current_user.cliente_id
    try:
        return await centro_costo_service.get_centro_costo_servicio(
            client_id=client_id,
            centro_costo_id=centro_costo_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("", response_model=CentroCostoRead, status_code=201, summary="Crear centro de costo")
async def crear_centro_costo(
    data: CentroCostoCreate,
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.area.leer")),
):
    client_id = current_user.cliente_id
    return await centro_costo_service.create_centro_costo_servicio(
        client_id=client_id,
        data=data,
    )


@router.put("/{centro_costo_id}", response_model=CentroCostoRead, summary="Actualizar centro de costo")
async def actualizar_centro_costo(
    centro_costo_id: UUID,
    data: CentroCostoUpdate,
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.area.actualizar")),
):
    client_id = current_user.cliente_id
    try:
        return await centro_costo_service.update_centro_costo_servicio(
            client_id=client_id,
            centro_costo_id=centro_costo_id,
            data=data,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
