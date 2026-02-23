"""Endpoints mrp_necesidad_bruta."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.mrp.application.services import (
    list_necesidad_bruta,
    get_necesidad_bruta_by_id,
    create_necesidad_bruta,
    update_necesidad_bruta,
)
from app.modules.mrp.presentation.schemas import NecesidadBrutaCreate, NecesidadBrutaUpdate, NecesidadBrutaRead
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[NecesidadBrutaRead], tags=["MRP - Necesidades Brutas"])
async def get_necesidades_brutas(
    plan_maestro_id: Optional[UUID] = Query(None),
    producto_id: Optional[UUID] = Query(None),
    origen: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await list_necesidad_bruta(
        current_user.cliente_id,
        plan_maestro_id=plan_maestro_id,
        producto_id=producto_id,
        origen=origen,
    )


@router.get("/{necesidad_id}", response_model=NecesidadBrutaRead, tags=["MRP - Necesidades Brutas"])
async def get_necesidad_bruta(
    necesidad_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    try:
        return await get_necesidad_bruta_by_id(current_user.cliente_id, necesidad_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=NecesidadBrutaRead, status_code=status.HTTP_201_CREATED, tags=["MRP - Necesidades Brutas"])
async def post_necesidad_bruta(
    data: NecesidadBrutaCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await create_necesidad_bruta(current_user.cliente_id, data)


@router.put("/{necesidad_id}", response_model=NecesidadBrutaRead, tags=["MRP - Necesidades Brutas"])
async def put_necesidad_bruta(
    necesidad_id: UUID,
    data: NecesidadBrutaUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    try:
        return await update_necesidad_bruta(current_user.cliente_id, necesidad_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
