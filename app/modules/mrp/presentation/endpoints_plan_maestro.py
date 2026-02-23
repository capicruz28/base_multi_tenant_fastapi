"""Endpoints mrp_plan_maestro."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.mrp.application.services import (
    list_plan_maestro,
    get_plan_maestro_by_id,
    create_plan_maestro,
    update_plan_maestro,
)
from app.modules.mrp.presentation.schemas import PlanMaestroCreate, PlanMaestroUpdate, PlanMaestroRead
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[PlanMaestroRead], tags=["MRP - Plan Maestro"])
async def get_planes_maestro(
    empresa_id: Optional[UUID] = Query(None),
    estado: Optional[str] = Query(None),
    buscar: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await list_plan_maestro(
        current_user.cliente_id,
        empresa_id=empresa_id,
        estado=estado,
        buscar=buscar,
    )


@router.get("/{plan_maestro_id}", response_model=PlanMaestroRead, tags=["MRP - Plan Maestro"])
async def get_plan_maestro(
    plan_maestro_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    try:
        return await get_plan_maestro_by_id(current_user.cliente_id, plan_maestro_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=PlanMaestroRead, status_code=status.HTTP_201_CREATED, tags=["MRP - Plan Maestro"])
async def post_plan_maestro(
    data: PlanMaestroCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await create_plan_maestro(current_user.cliente_id, data)


@router.put("/{plan_maestro_id}", response_model=PlanMaestroRead, tags=["MRP - Plan Maestro"])
async def put_plan_maestro(
    plan_maestro_id: UUID,
    data: PlanMaestroUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    try:
        return await update_plan_maestro(current_user.cliente_id, plan_maestro_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
