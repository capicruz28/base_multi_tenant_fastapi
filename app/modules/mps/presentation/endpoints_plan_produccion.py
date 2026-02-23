"""Endpoints mps_plan_produccion."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.mps.application.services import (
    list_plan_produccion,
    get_plan_produccion_by_id,
    create_plan_produccion,
    update_plan_produccion,
)
from app.modules.mps.presentation.schemas import PlanProduccionCreate, PlanProduccionUpdate, PlanProduccionRead
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[PlanProduccionRead], tags=["MPS - Plan de Producción"])
async def get_planes_produccion(
    empresa_id: Optional[UUID] = Query(None),
    estado: Optional[str] = Query(None),
    buscar: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await list_plan_produccion(
        current_user.cliente_id,
        empresa_id=empresa_id,
        estado=estado,
        buscar=buscar,
    )


@router.get("/{plan_produccion_id}", response_model=PlanProduccionRead, tags=["MPS - Plan de Producción"])
async def get_plan_produccion(
    plan_produccion_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    try:
        return await get_plan_produccion_by_id(current_user.cliente_id, plan_produccion_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=PlanProduccionRead, status_code=status.HTTP_201_CREATED, tags=["MPS - Plan de Producción"])
async def post_plan_produccion(
    data: PlanProduccionCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await create_plan_produccion(current_user.cliente_id, data)


@router.put("/{plan_produccion_id}", response_model=PlanProduccionRead, tags=["MPS - Plan de Producción"])
async def put_plan_produccion(
    plan_produccion_id: UUID,
    data: PlanProduccionUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    try:
        return await update_plan_produccion(current_user.cliente_id, plan_produccion_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
