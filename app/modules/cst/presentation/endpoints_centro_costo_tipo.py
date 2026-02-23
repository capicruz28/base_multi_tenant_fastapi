"""Endpoints cst tipos de centro de costo."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.cst.application.services import (
    list_centro_costo_tipo,
    get_centro_costo_tipo_by_id,
    create_centro_costo_tipo,
    update_centro_costo_tipo,
)
from app.modules.cst.presentation.schemas import (
    CentroCostoTipoCreate,
    CentroCostoTipoUpdate,
    CentroCostoTipoRead,
)
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[CentroCostoTipoRead])
async def get_tipos_centro_costo(
    empresa_id: Optional[UUID] = Query(None),
    tipo_clasificacion: Optional[str] = Query(None),
    es_activo: Optional[bool] = Query(None),
    buscar: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await list_centro_costo_tipo(
        current_user.cliente_id,
        empresa_id=empresa_id,
        tipo_clasificacion=tipo_clasificacion,
        es_activo=es_activo,
        buscar=buscar,
    )


@router.get("/{cc_tipo_id}", response_model=CentroCostoTipoRead)
async def get_tipo_centro_costo(
    cc_tipo_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    try:
        return await get_centro_costo_tipo_by_id(current_user.cliente_id, cc_tipo_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=CentroCostoTipoRead, status_code=status.HTTP_201_CREATED)
async def post_tipo_centro_costo(
    data: CentroCostoTipoCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await create_centro_costo_tipo(current_user.cliente_id, data)


@router.put("/{cc_tipo_id}", response_model=CentroCostoTipoRead)
async def put_tipo_centro_costo(
    cc_tipo_id: UUID,
    data: CentroCostoTipoUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    try:
        return await update_centro_costo_tipo(current_user.cliente_id, cc_tipo_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
