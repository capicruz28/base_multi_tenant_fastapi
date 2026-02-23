"""Endpoints mnt_activo."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.mnt.application.services import (
    list_activo,
    get_activo_by_id,
    create_activo,
    update_activo,
)
from app.modules.mnt.presentation.schemas import ActivoCreate, ActivoUpdate, ActivoRead
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[ActivoRead], tags=["MNT - Activos"])
async def get_activos(
    empresa_id: Optional[UUID] = Query(None),
    tipo_activo: Optional[str] = Query(None),
    estado_activo: Optional[str] = Query(None),
    criticidad: Optional[str] = Query(None),
    es_activo: Optional[bool] = Query(None),
    buscar: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await list_activo(
        current_user.cliente_id,
        empresa_id=empresa_id,
        tipo_activo=tipo_activo,
        estado_activo=estado_activo,
        criticidad=criticidad,
        es_activo=es_activo,
        buscar=buscar,
    )


@router.get("/{activo_id}", response_model=ActivoRead, tags=["MNT - Activos"])
async def get_activo(
    activo_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    try:
        return await get_activo_by_id(current_user.cliente_id, activo_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=ActivoRead, status_code=status.HTTP_201_CREATED, tags=["MNT - Activos"])
async def post_activo(
    data: ActivoCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await create_activo(current_user.cliente_id, data)


@router.put("/{activo_id}", response_model=ActivoRead, tags=["MNT - Activos"])
async def put_activo(
    activo_id: UUID,
    data: ActivoUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    try:
        return await update_activo(current_user.cliente_id, activo_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
