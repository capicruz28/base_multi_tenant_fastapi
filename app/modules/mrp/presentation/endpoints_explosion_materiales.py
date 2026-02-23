"""Endpoints mrp_explosion_materiales."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.mrp.application.services import (
    list_explosion_materiales,
    get_explosion_materiales_by_id,
    create_explosion_materiales,
    update_explosion_materiales,
)
from app.modules.mrp.presentation.schemas import (
    ExplosionMaterialesCreate,
    ExplosionMaterialesUpdate,
    ExplosionMaterialesRead,
)
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[ExplosionMaterialesRead], tags=["MRP - Explosión Materiales"])
async def get_explosiones_materiales(
    plan_maestro_id: Optional[UUID] = Query(None),
    producto_componente_id: Optional[UUID] = Query(None),
    nivel_bom: Optional[int] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await list_explosion_materiales(
        current_user.cliente_id,
        plan_maestro_id=plan_maestro_id,
        producto_componente_id=producto_componente_id,
        nivel_bom=nivel_bom,
    )


@router.get("/{explosion_id}", response_model=ExplosionMaterialesRead, tags=["MRP - Explosión Materiales"])
async def get_explosion_materiales(
    explosion_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    try:
        return await get_explosion_materiales_by_id(current_user.cliente_id, explosion_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=ExplosionMaterialesRead, status_code=status.HTTP_201_CREATED, tags=["MRP - Explosión Materiales"])
async def post_explosion_materiales(
    data: ExplosionMaterialesCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await create_explosion_materiales(current_user.cliente_id, data)


@router.put("/{explosion_id}", response_model=ExplosionMaterialesRead, tags=["MRP - Explosión Materiales"])
async def put_explosion_materiales(
    explosion_id: UUID,
    data: ExplosionMaterialesUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    try:
        return await update_explosion_materiales(current_user.cliente_id, explosion_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
